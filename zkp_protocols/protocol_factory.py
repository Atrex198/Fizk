"""
ZKP Protocol Factory
===================

Factory for creating different ZKP protocol instances
following the unified architecture design.
"""

from typing import Dict, Any, List
from .base import IZKPProtocol, ProtocolType

class ZKPProtocolFactory:
    """Factory for creating protocol instances"""
    
    _protocols = {
        ProtocolType.PROTOSTAR: 'ProductionProtostar',
        ProtocolType.BULLETPROOFS: 'BulletproofsProtocol',
        # Add other protocols as they are implemented
        # ProtocolType.PLONK: 'PLONKProtocol',
        # ProtocolType.GROTH16: 'Groth16Protocol',
        # ProtocolType.NOVA: 'NovaProtocol'
    }
    
    @staticmethod
    def create_protocol(
        protocol_type: ProtocolType,
        config: Dict[str, Any]
    ) -> IZKPProtocol:
        """
        Create protocol instance
        
        Args:
            protocol_type: Type of protocol to create
            config: Protocol configuration
        
        Returns:
            IZKPProtocol implementation
        """
        if protocol_type not in ZKPProtocolFactory._protocols:
            available = list(ZKPProtocolFactory._protocols.keys())
            raise ValueError(f"Protocol {protocol_type} not supported. Available: {available}")
        
        protocol_class_name = ZKPProtocolFactory._protocols[protocol_type]
        
        # Import the appropriate protocol class
        if protocol_type == ProtocolType.PROTOSTAR:
            from .protostar_production import ProductionProtostar
            return ProductionProtostar(config)
        elif protocol_type == ProtocolType.BULLETPROOFS:
            from .bulletproofs_protocol import BulletproofsProtocol
            return BulletproofsProtocol(config)
        # Add other protocols as needed
        else:
            raise NotImplementedError(f"Protocol {protocol_type} factory not implemented yet")
    
    @staticmethod
    def get_available_protocols() -> List[ProtocolType]:
        """Get list of available protocols"""
        return list(ZKPProtocolFactory._protocols.keys())
    
    @staticmethod
    def get_protocol_info(protocol_type: ProtocolType) -> Dict[str, Any]:
        """
        Get basic information about a protocol without instantiating it
        
        Args:
            protocol_type: Protocol type to get info for
            
        Returns:
            Basic protocol information
        """
        protocol_info = {
            ProtocolType.PROTOSTAR: {
                'name': 'ProtoStar',
                'description': 'Production-grade ProtoStar with ProtoGalaxy aggregation',
                'trusted_setup': True,
                'proof_size': '~2KB',
                'verification_time': '~1ms',
                'features': ['IVC', 'Folding', 'Aggregation']
            },
            ProtocolType.BULLETPROOFS: {
                'name': 'Bulletproofs',
                'description': 'Zero-knowledge proofs with transparent setup',
                'trusted_setup': False,
                'proof_size': '~1-2KB',
                'verification_time': '~20ms',
                'features': ['No trusted setup', 'Range proofs', 'Batch verification']
            }
        }
        
        return protocol_info.get(protocol_type, {
            'name': str(protocol_type),
            'description': 'Protocol information not available',
            'trusted_setup': 'Unknown',
            'proof_size': 'Unknown',
            'verification_time': 'Unknown',
            'features': []
        })
    
    @staticmethod
    def compare_protocols() -> Dict[str, Any]:
        """
        Compare available protocols
        
        Returns:
            Comparison table of all available protocols
        """
        comparison = {
            'protocols': [],
            'comparison_criteria': [
                'trusted_setup_required',
                'proof_size_estimate',
                'verification_time_estimate',
                'transparency',
                'aggregation_support'
            ]
        }
        
        for protocol_type in ZKPProtocolFactory.get_available_protocols():
            info = ZKPProtocolFactory.get_protocol_info(protocol_type)
            comparison['protocols'].append({
                'type': protocol_type.value,
                'name': info['name'],
                'trusted_setup_required': info.get('trusted_setup', 'Unknown'),
                'proof_size_estimate': info.get('proof_size', 'Unknown'),
                'verification_time_estimate': info.get('verification_time', 'Unknown'),
                'transparency': 'Full' if not info.get('trusted_setup') else 'Setup dependent',
                'aggregation_support': 'Yes' if 'Aggregation' in info.get('features', []) else 'Batch verification',
                'features': info.get('features', [])
            })
        
        return comparison