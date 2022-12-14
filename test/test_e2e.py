"""
End to end tests
"""
import unittest

import pytest
from confluent_kafka import Consumer
from stomp import Connection


@pytest.fixture
def amq_connection() -> Connection:
    conn = Connection()
    conn.connect("admin", "admin")
    return conn


@pytest.fixture
def kafka_consumer() -> Consumer:
    consumer = Consumer({
        "bootstrap.servers": "localhost:29092",
        "group.id": "test",
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe(["detected-runs"])
    return consumer


def test_end_to_end_run_should_be_processed(amq_connection: Connection, kafka_consumer: Consumer) -> None:
    """
    Test message that is sent to activemq is processed and arrives at kafka instance
    :return: None
    """

    amq_connection.send("Interactive-Reduction", r"\\isis\inst$\cycle_22_4\NDXGEM\GEM92450.nxs")

    for _ in range(60):
        
        msg = kafka_consumer.poll(timeout=1.0)
        print(msg)
        if msg is None:
            continue
        if msg.error():
            pytest.fail("Failed to consume from broker")
        try:
            assert msg.value() == br"\\isis\inst$\cycle_22_4\NDXGEM\GEM92450.nxs"
        finally:
            kafka_consumer.close()
        break
    else:
        kafka_consumer.close()
        pytest.fail("Message was never consumed")


def test_end_to_end_run_should_not_be_processed() -> None:
    """
    Test message that is sent to activemq does not arrive at kafka instance
    :return: None
    """
    # This needs to be implemented when rules and specifications are implemented


if __name__ == '__main__':
    unittest.main()
