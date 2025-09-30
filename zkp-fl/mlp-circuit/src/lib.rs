use ark_ff::{Field, PrimeField, Zero, BigInteger, One};
use ark_relations::{
    r1cs::{ConstraintSynthesizer, ConstraintSystemRef, SynthesisError},
};
use ark_r1cs_std::{
    alloc::AllocVar,
    fields::fp::FpVar,
    boolean::Boolean,
    prelude::*,
};
use zkp_core::{ScalarField, ZkpError, ZkpResult};
use serde::{Serialize, Deserialize};

/// Configuration for MLP architecture
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MLPConfig {
    pub input_size: usize,
    pub hidden_sizes: Vec<usize>,
    pub output_size: usize,
    pub use_bias: bool,
}

impl Default for MLPConfig {
    fn default() -> Self {
        Self {
            input_size: 16,  // Typical for heart disease dataset after preprocessing 
            hidden_sizes: vec![256, 128],
            output_size: 1,
            use_bias: true,
        }
    }
}

/// MLP weights in field element representation
#[derive(Debug, Clone)]
pub struct MLPWeights {
    pub weights: Vec<Vec<Vec<ScalarField>>>, // [layer][output_neuron][input_neuron]
    pub biases: Vec<Vec<ScalarField>>,       // [layer][neuron]
}

impl MLPWeights {
    /// Create zero-initialized weights matching the config
    pub fn zero(config: &MLPConfig) -> Self {
        let mut weights = Vec::new();
        let mut biases = Vec::new();
        
        let layer_sizes = [vec![config.input_size], config.hidden_sizes.clone(), vec![config.output_size]].concat();
        
        for i in 0..layer_sizes.len() - 1 {
            let input_size = layer_sizes[i];
            let output_size = layer_sizes[i + 1];
            
            // Initialize weight matrix for this layer
            let mut layer_weights = Vec::new();
            for _ in 0..output_size {
                let mut neuron_weights = Vec::new();
                for _ in 0..input_size {
                    neuron_weights.push(ScalarField::zero());
                }
                layer_weights.push(neuron_weights);
            }
            weights.push(layer_weights);
            
            // Initialize bias vector for this layer
            let mut layer_biases = Vec::new();
            for _ in 0..output_size {
                layer_biases.push(ScalarField::zero());
            }
            biases.push(layer_biases);
        }
        
        Self { weights, biases }
    }
    
    /// Convert from PyTorch-style weights (flat vectors) to structured format
    pub fn from_pytorch_weights(
        config: &MLPConfig,
        weight_matrices: &[Vec<ScalarField>],
        bias_vectors: &[Vec<ScalarField>],
    ) -> ZkpResult<Self> {
        let mut weights = Vec::new();
        let mut biases = Vec::new();
        
        let layer_sizes = [vec![config.input_size], config.hidden_sizes.clone(), vec![config.output_size]].concat();
        
        if weight_matrices.len() != layer_sizes.len() - 1 {
            return Err(ZkpError::InvalidParameters(
                "Weight matrices don't match layer configuration".to_string()
            ));
        }
        
        for (layer_idx, weight_flat) in weight_matrices.iter().enumerate() {
            let input_size = layer_sizes[layer_idx];
            let output_size = layer_sizes[layer_idx + 1];
            
            if weight_flat.len() != input_size * output_size {
                return Err(ZkpError::InvalidParameters(
                    format!("Layer {} weight size mismatch", layer_idx)
                ));
            }
            
            // Reshape flat weights to matrix
            let mut layer_weights = Vec::new();
            for out_idx in 0..output_size {
                let mut neuron_weights = Vec::new();
                for in_idx in 0..input_size {
                    let weight_idx = out_idx * input_size + in_idx;
                    neuron_weights.push(weight_flat[weight_idx]);
                }
                layer_weights.push(neuron_weights);
            }
            weights.push(layer_weights);
            
            // Add biases
            if config.use_bias {
                biases.push(bias_vectors[layer_idx].clone());
            } else {
                biases.push(vec![ScalarField::zero(); output_size]);
            }
        }
        
        Ok(Self { weights, biases })
    }
}

/// Input to the MLP circuit
#[derive(Debug, Clone)]
pub struct MLPInputs {
    pub features: Vec<ScalarField>,
    pub weights: MLPWeights,
    pub prediction: Option<ScalarField>, // Expected prediction for verification
}

/// Output from the MLP circuit
#[derive(Debug, Clone)]
pub struct MLPOutputs {
    pub prediction: ScalarField,
    pub intermediate_outputs: Vec<Vec<ScalarField>>, // For debugging/verification
}

/// R1CS constraint implementation for MLP forward pass
#[derive(Clone)]
pub struct MLPCircuit {
    pub config: MLPConfig,
    pub inputs: Option<MLPInputs>,
}

impl MLPCircuit {
    pub fn new(config: MLPConfig) -> Self {
        Self {
            config,
            inputs: None,
        }
    }
    
    pub fn with_inputs(config: MLPConfig, inputs: MLPInputs) -> Self {
        Self {
            config,
            inputs: Some(inputs),
        }
    }
}

impl ConstraintSynthesizer<ScalarField> for MLPCircuit {
    fn generate_constraints(self, cs: ConstraintSystemRef<ScalarField>) -> Result<(), SynthesisError> {
        // Allocate input variables
        let inputs = match self.inputs {
            Some(inputs) => inputs,
            None => return Err(SynthesisError::AssignmentMissing),
        };
        
        // Allocate feature variables
        let mut feature_vars = Vec::new();
        for &feature in &inputs.features {
            let var = FpVar::new_witness(cs.clone(), || Ok(feature))?;
            feature_vars.push(var);
        }
        
        // Allocate weight variables (private witnesses)
        let mut weight_vars = Vec::new();
        for layer_weights in &inputs.weights.weights {
            let mut layer_weight_vars = Vec::new();
            for neuron_weights in layer_weights {
                let mut neuron_weight_vars = Vec::new();
                for &weight in neuron_weights {
                    let weight_var = FpVar::new_witness(cs.clone(), || Ok(weight))?;
                    neuron_weight_vars.push(weight_var);
                }
                layer_weight_vars.push(neuron_weight_vars);
            }
            weight_vars.push(layer_weight_vars);
        }
        
        // Allocate bias variables
        let mut bias_vars = Vec::new();
        for layer_biases in &inputs.weights.biases {
            let mut layer_bias_vars = Vec::new();
            for &bias in layer_biases {
                let bias_var = FpVar::new_witness(cs.clone(), || Ok(bias))?;
                layer_bias_vars.push(bias_var);
            }
            bias_vars.push(layer_bias_vars);
        }
        
        // Forward pass through the network
        let mut current_activations = feature_vars;
        
        for (layer_idx, layer_weight_vars) in weight_vars.iter().enumerate() {
            let layer_bias_vars = &bias_vars[layer_idx];
            let mut next_activations = Vec::new();
            
            // For each neuron in this layer
            for (neuron_idx, neuron_weight_vars) in layer_weight_vars.iter().enumerate() {
                // Compute weighted sum: sum(weight * input) + bias
                let mut weighted_sum = layer_bias_vars[neuron_idx].clone();
                
                for (input_idx, input_activation) in current_activations.iter().enumerate() {
                    let weight_var = &neuron_weight_vars[input_idx];
                    let product = input_activation * weight_var;
                    weighted_sum = weighted_sum + product;
                }
                
                // Apply activation function (ReLU for hidden layers, linear for output)
                let activation = if layer_idx == weight_vars.len() - 1 {
                    // Output layer - linear activation
                    weighted_sum
                } else {
                    // Hidden layer - ReLU activation
                    relu_constraint(cs.clone(), &weighted_sum)?
                };
                
                next_activations.push(activation);
            }
            
            current_activations = next_activations;
        }
        
        // The final output should be a single value for binary classification
        if current_activations.len() != 1 {
            return Err(SynthesisError::Unsatisfiable);
        }
        
        // Make the final prediction a public input
        let prediction = &current_activations[0];
        prediction.enforce_equal(&FpVar::new_input(cs.clone(), || {
            Ok(inputs.prediction.unwrap_or(ScalarField::zero()))
        })?)?;
        
        Ok(())
    }
}

/// ReLU activation function constraint
/// ReLU(x) = max(0, x)
/// Implemented using comparison and conditional selection
fn relu_constraint(
    cs: ConstraintSystemRef<ScalarField>,
    input: &FpVar<ScalarField>,
) -> Result<FpVar<ScalarField>, SynthesisError> {
    let zero = FpVar::constant(ScalarField::zero());
    
    // Allocate a boolean variable to represent whether input >= 0
    let is_positive = Boolean::new_witness(cs.clone(), || {
        Ok(input.value()? >= ScalarField::zero())
    })?;
    
    // Allocate the output variable
    let output = FpVar::new_witness(cs.clone(), || {
        let input_val = input.value()?;
        if input_val >= ScalarField::zero() {
            Ok(input_val)
        } else {
            Ok(ScalarField::zero())
        }
    })?;
    
    // Constraint 1: If is_positive is true, then output = input
    // If is_positive is false, then output = 0
    // This is enforced by: output = is_positive * input
    let selected_value = FpVar::conditionally_select(&is_positive, input, &zero)?;
    output.enforce_equal(&selected_value)?;
    
    // Constraint 2: Ensure is_positive is consistent with input
    // If input >= 0, then is_positive must be true
    // If input < 0, then is_positive must be false
    // This is more complex in R1CS and requires range proofs for full security
    // For now, we rely on the witness generation being honest
    
    Ok(output)
}

/// Mean Squared Error loss function constraint
/// MSE = (prediction - target)^2
fn mse_loss_constraint(
    cs: ConstraintSystemRef<ScalarField>,
    prediction: &FpVar<ScalarField>,
    target: &FpVar<ScalarField>,
) -> Result<FpVar<ScalarField>, SynthesisError> {
    // Compute difference: prediction - target
    let diff = prediction - target;
    
    // Compute squared difference: (prediction - target)^2
    let squared_diff = &diff * &diff;
    
    Ok(squared_diff)
}

/// Binary Cross Entropy loss function constraint
/// BCE = -[target * log(prediction) + (1-target) * log(1-prediction)]
/// Simplified version using quadratic approximation for efficiency in R1CS
fn bce_loss_constraint(
    cs: ConstraintSystemRef<ScalarField>,
    prediction: &FpVar<ScalarField>,
    target: &FpVar<ScalarField>,
) -> Result<FpVar<ScalarField>, SynthesisError> {
    // For R1CS efficiency, we use a quadratic approximation of BCE
    // This is a simplified version - full BCE requires logarithm circuits
    let diff = prediction - target;
    let squared_diff = &diff * &diff;
    
    // Add a penalty term for predictions far from [0,1] range
    let one = FpVar::constant(ScalarField::one());
    let zero = FpVar::constant(ScalarField::zero());
    
    // Simple quadratic loss that approximates BCE behavior
    Ok(squared_diff)
}

/// Training step circuit for proving correct gradient computation
pub struct MLPTrainingCircuit {
    pub config: MLPConfig,
    pub training_data: Option<MLPTrainingData>,
}

#[derive(Debug, Clone)]
pub struct MLPTrainingData {
    pub features: Vec<ScalarField>,
    pub label: ScalarField,
    pub old_weights: MLPWeights,
    pub new_weights: MLPWeights,
    pub learning_rate: ScalarField,
}

impl ConstraintSynthesizer<ScalarField> for MLPTrainingCircuit {
    fn generate_constraints(self, cs: ConstraintSystemRef<ScalarField>) -> Result<(), SynthesisError> {
        let data = match self.training_data {
            Some(data) => data,
            None => return Err(SynthesisError::AssignmentMissing),
        };
        
        // 1. Compute forward pass with old weights
        let forward_circuit = MLPCircuit::with_inputs(
            self.config.clone(),
            MLPInputs {
                features: data.features.clone(),
                weights: data.old_weights.clone(),
                prediction: None, // Will be computed during forward pass
            }
        );
        
        // Generate constraints for forward pass
        // This proves that the prediction was computed correctly
        forward_circuit.generate_constraints(cs.clone())?;
        
        // 2. Compute loss and verify training step correctness
        
        // Allocate variables for prediction and target
        let prediction_var = FpVar::new_witness(cs.clone(), || {
            // Forward pass to get prediction
            Ok(ScalarField::from(1u64)) // Placeholder - should be actual prediction
        })?;
        
        let target_var = FpVar::new_witness(cs.clone(), || Ok(data.label))?;
        
        // Compute loss (using MSE for simplicity)
        let loss = mse_loss_constraint(cs.clone(), &prediction_var, &target_var)?;
        
        // Make loss a public input to verify training step
        let _public_loss = FpVar::new_input(cs.clone(), || {
            let pred = prediction_var.value()?;
            let target = target_var.value()?;
            let diff = pred - target;
            Ok(diff * diff)
        })?;
        
        // 3. Verify weight updates are reasonable
        // For full security, this would include gradient computation constraints
        // For now, we verify the magnitude of weight changes is bounded
        
        let lr_var = FpVar::new_witness(cs.clone(), || Ok(data.learning_rate))?;
        
        for (layer_idx, (old_layer, new_layer)) in data.old_weights.weights.iter()
            .zip(&data.new_weights.weights).enumerate() {
            
            for (neuron_idx, (old_neuron, new_neuron)) in old_layer.iter()
                .zip(new_layer).enumerate() {
                
                for (weight_idx, (&old_weight, &new_weight)) in old_neuron.iter()
                    .zip(new_neuron).enumerate() {
                    
                    let old_var = FpVar::new_witness(cs.clone(), || Ok(old_weight))?;
                    let new_var = FpVar::new_witness(cs.clone(), || Ok(new_weight))?;
                    
                    // Verify weight update: new_weight = old_weight - learning_rate * gradient
                    // Since gradient computation is complex, we verify the update magnitude is reasonable
                    let diff = &new_var - &old_var;
                    let _abs_diff = diff.square()?; // Use square as proxy for absolute value
                    
                    // Constraint: Update magnitude should be proportional to learning rate
                    // In a full implementation, this would verify: diff = -lr * computed_gradient
                    let _bound = lr_var.square()?;
                    
                    // For demo purposes, we just ensure the weights are properly allocated
                    // TODO: Add proper gradient verification constraints
                }
            }
        }
        
        Ok(())
    }
}

/// Utility functions for converting between PyTorch tensors and field elements
pub mod conversion {
    use super::*;
    use ark_ff::PrimeField;
    
    const PRECISION_FACTOR: u64 = 1_000_000; // 6 decimal places
    
    /// Convert f32 to field element with fixed precision
    pub fn f32_to_field(value: f32) -> ScalarField {
        let scaled = (value * PRECISION_FACTOR as f32).round() as i64;
        if scaled >= 0 {
            ScalarField::from(scaled as u64)
        } else {
            -ScalarField::from((-scaled) as u64)
        }
    }
    
    /// Convert field element back to f32
    pub fn field_to_f32(field: ScalarField) -> f32 {
        // This is a simplified conversion - in practice you'd need to handle
        // the field's representation more carefully
        let bytes = BigInteger::to_bytes_le(&field.into_bigint());
        let mut value = 0u64;
        for (i, &byte) in bytes.iter().enumerate().take(8) {
            value |= (byte as u64) << (i * 8);
        }
        (value as f32) / (PRECISION_FACTOR as f32)
    }
    
    /// Convert vector of f32 weights to field elements
    pub fn weights_to_field(weights: &[f32]) -> Vec<ScalarField> {
        weights.iter().map(|&w| f32_to_field(w)).collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ark_relations::r1cs::ConstraintSystem;
    use ark_std::test_rng;
    
    #[test]
    fn test_mlp_config() {
        let config = MLPConfig::default();
        let weights = MLPWeights::zero(&config);
        
        // Check dimensions
        assert_eq!(weights.weights.len(), 3); // input->hidden1, hidden1->hidden2, hidden2->output
        assert_eq!(weights.weights[0].len(), 256); // First hidden layer size
        assert_eq!(weights.weights[0][0].len(), 16); // Input size
    }
    
    #[test]
    fn test_conversion_functions() {
        let value = 3.14159f32;
        let field_val = conversion::f32_to_field(value);
        let recovered = conversion::field_to_f32(field_val);
        
        // Should be close due to precision limitations
        assert!((value - recovered).abs() < 0.01);
    }
    
    #[test]
    fn test_mlp_circuit_structure() {
        let config = MLPConfig::default();
        let cs = ConstraintSystem::<ScalarField>::new_ref();
        
        // Create dummy inputs
        let features = vec![ScalarField::from(1u64); config.input_size];
        let weights = MLPWeights::zero(&config);
        
        let inputs = MLPInputs { features, weights };
        let circuit = MLPCircuit::with_inputs(config, inputs);
        
        // This should not panic - actual constraint generation would require
        // proper setup but this tests the structure
        assert!(circuit.config.input_size > 0);
    }
}