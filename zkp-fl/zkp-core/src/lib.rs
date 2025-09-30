use ark_ff::{Field, PrimeField, One, Zero};
use thiserror::Error;

pub type ScalarField = ark_bn254::Fr;

#[derive(Error, Debug)]
pub enum ZkpError {
    #[error("Circuit constraint error: {0}")]
    ConstraintError(String),
    #[error("Proof generation failed: {0}")]
    ProofGenerationError(String),
    #[error("Verification failed: {0}")]
    VerificationError(String),
    #[error("Serialization error: {0}")]
    SerializationError(String),
    #[error("Invalid parameters: {0}")]
    InvalidParameters(String),
}

pub type ZkpResult<T> = Result<T, ZkpError>;
