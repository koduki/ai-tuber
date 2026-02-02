import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from .config import ADK_TELEMETRY, logger

def setup_telemetry():
    """
    Sets up ADK Telemetry using ConsoleSpanExporter if enabled via environment variable.
    """
    if not ADK_TELEMETRY:
        return

    logger.info("Initializing ADK Telemetry (ConsoleSpanExporter)...")
    
    # Initialize TracerProvider
    provider = TracerProvider()
    
    # Configure ConsoleSpanExporter
    # We use SimpleSpanProcessor for immediate output to console
    processor = SimpleSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    
    # Set the global tracer provider
    trace.set_tracer_provider(provider)
    
    logger.info("ADK Telemetry initialized.")
