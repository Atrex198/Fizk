//! Rust ZKP bindings for Python
//!
//! This module provides Python bindings for various ZKP systems:
//! - PLONK (via Halo2)
//! - Bulletproofs
//! - Nova (folding schemes)
//! - Additional arkworks-based systems

use pyo3::prelude::*;
use pyo3::types::PyBytes;

mod plonk;
mod bulletproofs;
mod nova;

/// Initialize the Python module
#[pymodule]
fn zkp_bindings(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<plonk::PlonkProver>()?;
    m.add_class::<bulletproofs::BulletproofsProver>()?;
    m.add_class::<nova::NovaProver>()?;
    Ok(())
}

/// Common error type for ZKP operations
#[derive(Debug)]
pub enum ZKPError {
    ProofGenerationFailed(String),
    VerificationFailed(String),
    InvalidInput(String),
}

impl std::fmt::Display for ZKPError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            ZKPError::ProofGenerationFailed(msg) => write!(f, "Proof generation failed: {}", msg),
            ZKPError::VerificationFailed(msg) => write!(f, "Verification failed: {}", msg),
            ZKPError::InvalidInput(msg) => write!(f, "Invalid input: {}", msg),
        }
    }
}

impl std::error::Error for ZKPError {}

impl From<ZKPError> for PyErr {
    fn from(err: ZKPError) -> PyErr {
        pyo3::exceptions::PyRuntimeError::new_err(err.to_string())
    }
}
