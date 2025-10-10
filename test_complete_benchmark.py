#!/usr/bin/env python3
"""
Test script for complete multi-protocol benchmark system
"""

import asyncio
import sys
import logging
from complete_multi_protocol_benchmark import ScalabilityBenchmarkConfig, ScalabilityBenchmarkRunner

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_minimal_benchmark():
    """Test with minimal configuration"""
    logger.info("🧪 Testing Complete Multi-Protocol Benchmark System")
    
    try:
        # Create minimal test configuration
        config = ScalabilityBenchmarkConfig(
            client_counts=[3],  # Just 3 clients for testing
            round_counts=[1],   # Just 1 round
            samples_per_client=[500],  # Small dataset
            security_levels=[128]  # One security level
        )
        
        logger.info("Configuration created successfully")
        logger.info(f"  Client counts: {config.client_counts}")
        logger.info(f"  Round counts: {config.round_counts}")
        logger.info(f"  Samples per client: {config.samples_per_client}")
        logger.info(f"  Security levels: {config.security_levels}")
        
        # Create benchmark runner
        runner = ScalabilityBenchmarkRunner(config)
        logger.info("Benchmark runner created successfully")
        
        # Just test initialization, not full run for now
        logger.info("✅ Complete benchmark system initialization successful!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        logger.error(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_minimal_benchmark())
    sys.exit(0 if success else 1)