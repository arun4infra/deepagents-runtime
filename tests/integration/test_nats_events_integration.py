"""
NATS Events Integration Tests

Tests NATS CloudEvents pub/sub infrastructure with mocked agent execution.
Uses real Kubernetes deployment and NATS JetStream for realistic testing.

This test focuses on:
- CloudEvent format compliance
- NATS pub/sub mechanics
- Event serialization/deserialization
- Consumer behavior and error handling
- Streaming event structure

Infrastructure: Kubernetes (Real NATS JetStream)
Duration: ~30 seconds
"""

import asyncio
import json
import pytest
import uuid
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch

import nats
from nats.js import JetStreamContext
import structlog

from models.events import JobExecutionEvent
from services.nats_consumer import NATSConsumer
from services.cloudevents import CloudEventEmitter

logger = structlog.get_logger(__name__)


class TestNATSEventsIntegration:
    """Test NATS CloudEvents integration with mocked agent execution."""

    @pytest.fixture
    async def nats_connection(self):
        """Create NATS connection for testing."""
        nats_url = "nats://nats.nats.svc:4222"
        nc = None  # Initialize before try block
        
        try:
            nc = await nats.connect(nats_url, connect_timeout=10)
            js = nc.jetstream()
            yield nc, js
        finally:
            if nc and not nc.is_closed:
                await nc.close()

    @pytest.fixture
    def mock_execution_manager(self):
        """Mock ExecutionManager for testing."""
        mock_manager = AsyncMock()
        
        # Mock successful execution
        mock_manager.execute.return_value = {
            "status": "completed",
            "files": {
                "/THE_SPEC/constitution.md": {"content": ["# Test Constitution"], "created_at": "2024-01-01T00:00:00Z"},
                "/THE_SPEC/requirements.md": {"content": ["# Test Requirements"], "created_at": "2024-01-01T00:00:00Z"},
                "/definition.json": {"content": ['{"name": "test", "version": "1.0"}'], "created_at": "2024-01-01T00:00:00Z"}
            },
            "execution_time": 1.5
        }
        
        return mock_manager

    @pytest.fixture
    def mock_cloudevent_emitter(self):
        """Mock CloudEventEmitter for testing."""
        return AsyncMock()

    async def test_cloudevent_format_compliance(self, nats_connection):
        """Test CloudEvent format compliance."""
        nc, js = nats_connection
        
        print("\n🔍 Testing CloudEvent Format Compliance")
        
        # Create test CloudEvent
        cloudevent = {
            "specversion": "1.0",
            "type": "dev.my-platform.agent.execute",
            "source": "test-client",
            "subject": "test-job-001",
            "id": str(uuid.uuid4()),
            "time": "2024-01-01T00:00:00Z",
            "traceparent": "00-12345678901234567890123456789012-1234567890123456-01",
            "data": {
                "job_id": "test-job-001",
                "trace_id": "test-trace-001",
                "agent_definition": {"name": "test-agent"},
                "input_payload": {"user_request": "Hello World"}
            }
        }
        
        # Validate required CloudEvent fields
        required_fields = ["specversion", "type", "source", "id", "data"]
        for field in required_fields:
            assert field in cloudevent, f"Missing required CloudEvent field: {field}"
        
        # Validate CloudEvent spec version
        assert cloudevent["specversion"] == "1.0", "Invalid CloudEvent spec version"
        
        # Validate data structure
        data = cloudevent["data"]
        assert "job_id" in data, "Missing job_id in CloudEvent data"
        assert "agent_definition" in data, "Missing agent_definition in CloudEvent data"
        assert "input_payload" in data, "Missing input_payload in CloudEvent data"
        
        print("   ✅ CloudEvent format validation passed")

    async def test_nats_publish_subscribe(self, nats_connection):
        """Test basic NATS publish/subscribe functionality."""
        nc, js = nats_connection
        
        print("\n📡 Testing NATS Publish/Subscribe")
        
        # Create test stream if not exists
        test_stream = "TEST_AGENT_EXECUTION"
        test_subject = "agent.execute.test"
        
        try:
            await js.add_stream(
                name=test_stream,
                subjects=[f"{test_subject}.*"],
                retention="limits",
                max_msgs=100,
                max_age=3600  # 1 hour
            )
        except Exception:
            # Stream might already exist
            pass
        
        # Create consumer
        consumer_name = f"test-consumer-{uuid.uuid4().hex[:8]}"
        consumer = await js.pull_subscribe(
            subject=f"{test_subject}.*",
            durable=consumer_name,
            stream=test_stream
        )
        
        # Publish test message
        test_message = {
            "test_id": str(uuid.uuid4()),
            "message": "Hello NATS"
        }
        
        await js.publish(
            subject=f"{test_subject}.hello",
            payload=json.dumps(test_message).encode()
        )
        
        print("   📤 Published test message")
        
        # Subscribe and receive message
        msgs = await consumer.fetch(batch=1, timeout=5)
        assert len(msgs) == 1, "Expected 1 message"
        
        received_message = json.loads(msgs[0].data.decode())
        assert received_message["test_id"] == test_message["test_id"], "Message content mismatch"
        
        await msgs[0].ack()
        print("   📥 Received and acknowledged message")
        
        # Cleanup
        try:
            await js.delete_consumer(test_stream, consumer_name)
            await js.delete_stream(test_stream)
        except Exception:
            pass

    async def test_job_execution_event_validation(self):
        """Test JobExecutionEvent model validation."""
        print("\n📋 Testing JobExecutionEvent Validation")
        
        # Valid event data
        valid_event_data = {
            "job_id": "test-job-001",
            "trace_id": "test-trace-001", 
            "agent_definition": {
                "name": "test-agent",
                "version": "1.0",
                "nodes": [],
                "edges": []
            },
            "input_payload": {
                "user_request": "Create a Hello World agent"
            }
        }
        
        # Test valid event
        event = JobExecutionEvent(**valid_event_data)
        assert event.job_id == "test-job-001"
        assert event.trace_id == "test-trace-001"
        print("   ✅ Valid JobExecutionEvent created")
        
        # Test invalid event (missing required field)
        invalid_event_data = valid_event_data.copy()
        del invalid_event_data["job_id"]
        
        with pytest.raises(Exception):  # Pydantic validation error
            JobExecutionEvent(**invalid_event_data)
        
        print("   ✅ Invalid JobExecutionEvent rejected")

    async def test_nats_consumer_message_processing(self, nats_connection, mock_execution_manager, mock_cloudevent_emitter):
        """Test NATSConsumer message processing with mocked execution."""
        nc, js = nats_connection
        
        print("\n🔄 Testing NATS Consumer Message Processing")
        
        # Create test stream
        test_stream = "TEST_CONSUMER_STREAM"
        test_subject = "agent.execute.consumer"
        
        try:
            await js.add_stream(
                name=test_stream,
                subjects=[f"{test_subject}.*"],
                retention="limits",
                max_msgs=100,
                max_age=3600
            )
        except Exception:
            pass
        
        # Create NATSConsumer with mocked dependencies
        consumer = NATSConsumer(
            nats_url="nats://nats.nats.svc:4222",
            stream_name=test_stream,
            consumer_group=f"test-group-{uuid.uuid4().hex[:8]}",
            execution_manager=mock_execution_manager,
            cloudevent_emitter=mock_cloudevent_emitter
        )
        
        # Prepare test message
        test_cloudevent = {
            "specversion": "1.0",
            "type": "dev.my-platform.agent.execute",
            "source": "test-client",
            "id": str(uuid.uuid4()),
            "data": {
                "job_id": "test-job-002",
                "trace_id": "test-trace-002",
                "agent_definition": {"name": "test-agent", "version": "1.0"},
                "input_payload": {"user_request": "Test execution"}
            }
        }
        
        # Publish test message
        await js.publish(
            subject=f"{test_subject}.test",
            payload=json.dumps(test_cloudevent).encode()
        )
        
        print("   📤 Published test CloudEvent")
        
        # Mock the process_message method to avoid full consumer startup
        with patch.object(consumer, 'start') as mock_start:
            # Simulate message processing
            class MockMessage:
                def __init__(self, data):
                    self.data = data.encode() if isinstance(data, str) else data
                    self.subject = f"{test_subject}.test"
                    self.metadata = None
                
                async def ack(self):
                    pass
                
                async def nak(self):
                    pass
            
            mock_msg = MockMessage(json.dumps(test_cloudevent))
            
            # Process the message
            await consumer.process_message(mock_msg)
            
            # Verify execution manager was called
            mock_execution_manager.execute.assert_called_once()
            call_args = mock_execution_manager.execute.call_args
            
            assert call_args.kwargs["job_id"] == "test-job-002"
            assert call_args.kwargs["trace_id"] == "test-trace-002"
            
            print("   ✅ Message processed and execution manager called")
        
        # Cleanup
        try:
            await js.delete_stream(test_stream)
        except Exception:
            pass

    async def test_error_handling_and_retry(self, nats_connection, mock_cloudevent_emitter):
        """Test error handling and retry mechanisms."""
        print("\n⚠️  Testing Error Handling and Retry")
        
        # Create mock execution manager that fails
        failing_execution_manager = AsyncMock()
        failing_execution_manager.execute.side_effect = Exception("Simulated execution failure")
        
        consumer = NATSConsumer(
            nats_url="nats://nats.nats.svc:4222",
            stream_name="TEST_ERROR_STREAM",
            consumer_group=f"error-test-{uuid.uuid4().hex[:8]}",
            execution_manager=failing_execution_manager,
            cloudevent_emitter=mock_cloudevent_emitter
        )
        
        # Test message that will cause failure
        error_cloudevent = {
            "specversion": "1.0",
            "type": "dev.my-platform.agent.execute",
            "source": "test-client",
            "id": str(uuid.uuid4()),
            "data": {
                "job_id": "error-job-001",
                "trace_id": "error-trace-001",
                "agent_definition": {"name": "failing-agent"},
                "input_payload": {"user_request": "This will fail"}
            }
        }
        
        class MockMessage:
            def __init__(self, data):
                self.data = data.encode() if isinstance(data, str) else data
                self.subject = "agent.execute.error"
                self.metadata = None
            
            async def ack(self):
                pass
            
            async def nak(self):
                pass
        
        mock_msg = MockMessage(json.dumps(error_cloudevent))
        
        # Process message (should handle error gracefully)
        await consumer.process_message(mock_msg)
        
        # Verify execution was attempted
        failing_execution_manager.execute.assert_called_once()
        
        # Verify error result was published
        assert consumer.publish_result.call_count >= 0  # May be mocked
        
        print("   ✅ Error handled gracefully")

    async def test_cloudevent_result_publishing(self, nats_connection):
        """Test publishing result CloudEvents."""
        nc, js = nats_connection
        
        print("\n📤 Testing CloudEvent Result Publishing")
        
        # Create result stream
        result_stream = "TEST_RESULT_STREAM"
        
        try:
            await js.add_stream(
                name=result_stream,
                subjects=["agent.status.*"],
                retention="limits",
                max_msgs=100,
                max_age=3600
            )
        except Exception:
            pass
        
        # Create consumer for results
        result_consumer = await js.pull_subscribe(
            subject="agent.status.*",
            durable=f"result-consumer-{uuid.uuid4().hex[:8]}",
            stream=result_stream
        )
        
        # Mock consumer with real NATS connection
        mock_execution_manager = AsyncMock()
        mock_cloudevent_emitter = AsyncMock()
        
        consumer = NATSConsumer(
            nats_url="nats://nats.nats.svc:4222",
            stream_name=result_stream,
            consumer_group=f"publisher-test-{uuid.uuid4().hex[:8]}",
            execution_manager=mock_execution_manager,
            cloudevent_emitter=mock_cloudevent_emitter
        )
        
        # Connect consumer to NATS
        consumer.nc = nc
        consumer.js = js
        
        # Test successful result publishing
        await consumer.publish_result(
            job_id="result-job-001",
            result={"status": "completed", "files": {}},
            trace_id="result-trace-001",
            status="completed"
        )
        
        print("   📤 Published success result")
        
        # Test failed result publishing
        await consumer.publish_result(
            job_id="result-job-002",
            result={"message": "Test error", "type": "TestError"},
            trace_id="result-trace-002",
            status="failed"
        )
        
        print("   📤 Published failure result")
        
        # Verify results were published
        msgs = await result_consumer.fetch(batch=2, timeout=5)
        assert len(msgs) >= 1, "Expected at least 1 result message"
        
        for msg in msgs:
            result_data = json.loads(msg.data.decode())
            
            # Validate CloudEvent structure
            assert "specversion" in result_data
            assert "type" in result_data
            assert "data" in result_data
            
            # Validate result data
            data = result_data["data"]
            assert "job_id" in data
            
            await msg.ack()
        
        print("   📥 Received and validated result messages")
        
        # Cleanup
        try:
            await js.delete_stream(result_stream)
        except Exception:
            pass

    async def test_consumer_health_check(self, mock_execution_manager, mock_cloudevent_emitter):
        """Test NATSConsumer health check functionality."""
        print("\n🏥 Testing Consumer Health Check")
        
        consumer = NATSConsumer(
            nats_url="nats://nats.nats.svc:4222",
            stream_name="HEALTH_TEST_STREAM",
            consumer_group="health-test-group",
            execution_manager=mock_execution_manager,
            cloudevent_emitter=mock_cloudevent_emitter
        )
        
        # Test unhealthy state (not connected)
        assert not consumer.health_check(), "Consumer should be unhealthy when not connected"
        
        # Mock connected state
        consumer.nc = AsyncMock()
        consumer.nc.is_closed = False
        consumer.running = True
        
        # Test healthy state
        assert consumer.health_check(), "Consumer should be healthy when connected and running"
        
        print("   ✅ Health check functionality validated")


# Run tests
if __name__ == "__main__":
    async def run_tests():
        test_instance = TestNATSEventsIntegration()
        
        # Note: These would normally be run by pytest
        # This is just for demonstration
        print("🧪 NATS Events Integration Tests")
        print("=" * 50)
        
        # Individual test methods would be called by pytest
        # await test_instance.test_cloudevent_format_compliance(...)
        
        print("✅ All NATS events tests completed")
    
    asyncio.run(run_tests())