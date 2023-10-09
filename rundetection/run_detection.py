"""
Main module for run detection
"""
import logging
import sys
import time
from pathlib import Path
from queue import SimpleQueue

from pika import BlockingConnection, ConnectionParameters
from pika.adapters.blocking_connection import BlockingChannel

from rundetection.ingest import ingest, JobRequest
from rundetection.specifications import InstrumentSpecification

file_handler = logging.FileHandler(filename="run-detection.log")
stdout_handler = logging.StreamHandler(stream=sys.stdout)
logging.basicConfig(
    handlers=[file_handler, stdout_handler],
    format="[%(asctime)s]-%(name)s-%(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def get_channel(exchange_name: str, queue_name: str) -> BlockingChannel:
    connection_parameters = ConnectionParameters("rabbit-mq", 5672)
    connection = BlockingConnection(connection_parameters)
    channel = connection.channel()
    channel.exchange_declare(exchange_name, exchange_type="direct")
    channel.queue_declare(queue_name)
    channel.queue_bind(queue_name, exchange_name, routing_key="")
    return channel


def process_message(message: str, notification_queue: SimpleQueue[JobRequest]) -> None:
    """
    Process the incoming message. If the message should result in an upstream notification, it will put the message on
    the given notification queue
    :param message: The message to process
    :param notification_queue: The notification queue to update
    :return: None
    """
    logger.info("Proccessing message: %s", message)
    data_path = Path(message)
    run = ingest(data_path)
    specification = InstrumentSpecification(run.instrument)
    specification.verify(run)
    if run.will_reduce:
        logger.info("specification met for run: %s", run)
        notification_queue.put(run)
        for request in run.additional_requests:
            notification_queue.put(request)
    else:
        logger.info("Specification not met, skipping run: %s", run)


def process_messages(channel: BlockingChannel, notification_queue: SimpleQueue[JobRequest]) -> None:
    """
    Given a list of messages and the notification queue, process each message, adding those which meet specifications to
    the notification queue
    :param messages: The list of messages
    :param notification_queue: The notification queue
    :return: None
    """
    for mf, _, __ in channel.consume("detected-runs"):
        try:
            process_message(mf.body.decode(), notification_queue)
        except Exception:
            logger.warning("Problem processing message: %s", mf.body.decode)
        finally:
            channel.basic_ack(mf.delivery_tag)


def process_notifications(channel: BlockingChannel, notification_queue: SimpleQueue[JobRequest]) -> None:
    """
    Produce messages until the notification queue is empty
    :param producer: The producer
    :param notification_queue: The notification queue
    :return: None
    """
    while not notification_queue.empty():
        detected_run = notification_queue.get()
        logger.info("Sending notification for run: %s", detected_run.run_number)
        channel.basic_publish("job_requests", "", detected_run.to_json_string().encode())


def start_run_detection() -> None:
    """
    Main Coroutine starts the producer and consumer in a loop
    :return: None
    """

    logger.info("Starting Run Detection")
    logger.info("Creating consumer")
    consumer_channel = get_channel("detected-runs", "detected-runs")

    logger.info("Creating producer")
    producer_channel = get_channel("job_requests", "job_requests")

    notification_queue: SimpleQueue[JobRequest] = SimpleQueue()
    logger.info("Starting loop...")
    try:
        while True:
            process_messages(consumer_channel, notification_queue)
            process_notifications(producer_channel, notification_queue)
            time.sleep(0.1)

    # pylint: disable = broad-except
    except Exception:
        logger.exception("Uncaught error occurred in main loop. Restarting in 30 seconds...")
        time.sleep(30)
        start_run_detection()


def verify_archive_access() -> None:
    """Log archive access"""
    if Path("/archive", "NDXALF").exists():
        logger.info("The archive has been mounted correctly, and can be accessed.")
    else:
        logger.error("The archive has not been mounted correctly, and cannot be accessed.")


def main() -> None:
    """
    Entry point for run detection
    :return: None
    """
    verify_archive_access()
    start_run_detection()


if __name__ == "__main__":
    main()
