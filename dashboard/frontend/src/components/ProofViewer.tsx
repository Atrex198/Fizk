import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  Shield, 
  Copy, 
  Check, 
  ChevronDown, 
  ChevronRight,
  Lock,
  Key,
  Hash,
  Clock,
  Fingerprint
} from 'lucide-react';
import clsx from 'clsx';

interface ProofViewerProps {
  isOpen: boolean;
  onClose: () => void;
  runId: string;
  clientId: string;
  proofFile: string;
  proofData: ProofData | null;
  isLoading: boolean;
}

interface ProofData {
  run_id: string;
  client_id: string;
  file: string;
  proof: {
    protocol_type: string;
    proof_data: {
      protocol: string;
      version: string;
      witness_commitment: ECPoint;
      witness_error_commitment: ECPoint;
      constraint_commitment: ECPoint;
      constraint_error_commitment: ECPoint;
      challenge: string;
      proof_nonce: string;
      proof_timestamp: number;
      srs_commitment: string;
      kzg_opening_proofs: {
        witness: KZGProof;
        constraint: KZGProof;
      };
      constraints?: {
        num_constraints: number;
      };
      cryptographic_properties?: {
        zero_knowledge: boolean;
        soundness: string;
        completeness: string;
      };
    };
  };
}

interface ECPoint {
  point_coords: [string, string];
  point_type: string;
  type: string;
  metadata: {
    degree: number;
    computed_from_violations?: boolean;
  };
  is_ec_point: boolean;
}

interface KZGProof {
  evaluation: number | string;
  evaluation_point: string;
  opening_proof: ECPoint;
  commitment: ECPoint;
}

export default function ProofViewer({ 
  isOpen, 
  onClose, 
  clientId, 
  proofFile, 
  proofData, 
  isLoading 
}: ProofViewerProps) {
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview', 'commitments']));

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  };

  const copyToClipboard = async (text: string, field: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const formatTimestamp = (ts: number): string => {
    // Handle nanosecond timestamps
    const ms = ts > 1e15 ? ts / 1e6 : ts > 1e12 ? ts / 1e3 : ts;
    return new Date(ms).toLocaleString();
  };

  if (!isOpen) return null;

  const proof = proofData?.proof?.proof_data;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed inset-4 md:inset-10 lg:inset-20 bg-zkp-dark-card border border-zkp-dark-border rounded-2xl z-50 overflow-hidden flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-zkp-dark-border bg-zkp-dark/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-zkp-primary to-zkp-secondary flex items-center justify-center">
                  <Shield className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">ZKP Proof Viewer</h2>
                  <p className="text-sm text-gray-400">
                    {clientId} / {proofFile}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-zkp-dark-border transition-colors"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {isLoading ? (
                <div className="flex items-center justify-center h-64">
                  <div className="w-8 h-8 border-2 border-zkp-primary border-t-transparent rounded-full animate-spin" />
                </div>
              ) : proof ? (
                <>
                  {/* Overview Section */}
                  <Section
                    title="Protocol Overview"
                    icon={<Lock className="w-4 h-4" />}
                    isExpanded={expandedSections.has('overview')}
                    onToggle={() => toggleSection('overview')}
                  >
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <InfoBox label="Protocol" value={proof.protocol} />
                      <InfoBox label="Version" value={proof.version} />
                      <InfoBox label="Type" value={proofData?.proof?.protocol_type || 'protostar'} />
                      <InfoBox 
                        label="Timestamp" 
                        value={formatTimestamp(proof.proof_timestamp)} 
                      />
                    </div>
                  </Section>

                  {/* Cryptographic Properties */}
                  {proof.cryptographic_properties && (
                    <Section
                      title="Cryptographic Properties"
                      icon={<Fingerprint className="w-4 h-4" />}
                      isExpanded={expandedSections.has('crypto')}
                      onToggle={() => toggleSection('crypto')}
                    >
                      <div className="grid grid-cols-3 gap-4">
                        <PropertyBadge 
                          label="Zero Knowledge" 
                          active={proof.cryptographic_properties.zero_knowledge} 
                        />
                        <PropertyBadge 
                          label="Soundness" 
                          active={true} 
                          value={proof.cryptographic_properties.soundness}
                        />
                        <PropertyBadge 
                          label="Completeness" 
                          active={true}
                          value={proof.cryptographic_properties.completeness}
                        />
                      </div>
                    </Section>
                  )}

                  {/* Commitments Section */}
                  <Section
                    title="Polynomial Commitments"
                    icon={<Key className="w-4 h-4" />}
                    isExpanded={expandedSections.has('commitments')}
                    onToggle={() => toggleSection('commitments')}
                  >
                    <div className="space-y-4">
                      <CommitmentCard
                        title="Witness Commitment"
                        commitment={proof.witness_commitment}
                        color="primary"
                        onCopy={copyToClipboard}
                        copiedField={copiedField}
                      />
                      <CommitmentCard
                        title="Witness Error Commitment"
                        commitment={proof.witness_error_commitment}
                        color="secondary"
                        onCopy={copyToClipboard}
                        copiedField={copiedField}
                      />
                      <CommitmentCard
                        title="Constraint Commitment"
                        commitment={proof.constraint_commitment}
                        color="accent"
                        onCopy={copyToClipboard}
                        copiedField={copiedField}
                      />
                      <CommitmentCard
                        title="Constraint Error Commitment"
                        commitment={proof.constraint_error_commitment}
                        color="warning"
                        onCopy={copyToClipboard}
                        copiedField={copiedField}
                      />
                    </div>
                  </Section>

                  {/* Challenge & Nonce */}
                  <Section
                    title="Fiat-Shamir Challenge"
                    icon={<Hash className="w-4 h-4" />}
                    isExpanded={expandedSections.has('challenge')}
                    onToggle={() => toggleSection('challenge')}
                  >
                    <div className="space-y-3">
                      <CopyableField
                        label="Challenge (β)"
                        value={proof.challenge}
                        fullValue={proof.challenge}
                        onCopy={copyToClipboard}
                        copiedField={copiedField}
                        fieldId="challenge"
                      />
                      <CopyableField
                        label="Proof Nonce"
                        value={proof.proof_nonce}
                        fullValue={proof.proof_nonce}
                        onCopy={copyToClipboard}
                        copiedField={copiedField}
                        fieldId="nonce"
                      />
                      <CopyableField
                        label="SRS Commitment"
                        value={proof.srs_commitment}
                        fullValue={proof.srs_commitment}
                        onCopy={copyToClipboard}
                        copiedField={copiedField}
                        fieldId="srs"
                      />
                    </div>
                  </Section>

                  {/* KZG Opening Proofs */}
                  <Section
                    title="KZG Opening Proofs"
                    icon={<Shield className="w-4 h-4" />}
                    isExpanded={expandedSections.has('kzg')}
                    onToggle={() => toggleSection('kzg')}
                  >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <KZGProofCard
                        title="Witness Opening"
                        proof={proof.kzg_opening_proofs.witness}
                      />
                      <KZGProofCard
                        title="Constraint Opening"
                        proof={proof.kzg_opening_proofs.constraint}
                      />
                    </div>
                  </Section>

                  {/* Raw JSON */}
                  <Section
                    title="Raw Proof Data"
                    icon={<Clock className="w-4 h-4" />}
                    isExpanded={expandedSections.has('raw')}
                    onToggle={() => toggleSection('raw')}
                  >
                    <pre className="bg-black/50 rounded-lg p-4 text-xs text-gray-300 overflow-x-auto max-h-96 overflow-y-auto font-mono">
                      {JSON.stringify(proofData?.proof, null, 2)}
                    </pre>
                  </Section>
                </>
              ) : (
                <div className="text-center text-gray-400 py-8">
                  Failed to load proof data
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

// Helper Components

interface SectionProps {
  title: string;
  icon: React.ReactNode;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

function Section({ title, icon, isExpanded, onToggle, children }: SectionProps) {
  return (
    <div className="bg-zkp-dark/50 rounded-xl border border-zkp-dark-border overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 hover:bg-zkp-dark-border/30 transition-colors"
      >
        <div className="flex items-center gap-2 text-white font-medium">
          <span className="text-zkp-primary">{icon}</span>
          {title}
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-400" />
        )}
      </button>
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="p-4 pt-0">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function InfoBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 bg-zkp-dark-bg rounded-lg border border-zkp-dark-border">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className="text-sm text-white font-mono">{value}</p>
    </div>
  );
}

function PropertyBadge({ label, active, value }: { label: string; active: boolean; value?: string }) {
  return (
    <div className={clsx(
      "p-3 rounded-lg border text-center",
      active 
        ? "bg-zkp-success/10 border-zkp-success/30" 
        : "bg-zkp-dark-bg border-zkp-dark-border"
    )}>
      <p className={clsx("text-sm font-medium", active ? "text-zkp-success" : "text-gray-400")}>
        {label}
      </p>
      {value && <p className="text-xs text-gray-500 mt-1">{value}</p>}
    </div>
  );
}

interface CommitmentCardProps {
  title: string;
  commitment: ECPoint;
  color: 'primary' | 'secondary' | 'accent' | 'warning';
  onCopy: (text: string, field: string) => void;
  copiedField: string | null;
}

function CommitmentCard({ title, commitment, color, onCopy, copiedField }: CommitmentCardProps) {
  const colorClasses = {
    primary: 'border-zkp-primary/30 bg-zkp-primary/5',
    secondary: 'border-zkp-secondary/30 bg-zkp-secondary/5',
    accent: 'border-zkp-accent/30 bg-zkp-accent/5',
    warning: 'border-zkp-warning/30 bg-zkp-warning/5',
  };

  const fieldId = `${title}-coords`;
  const fullCoords = `(${commitment.point_coords[0]}, ${commitment.point_coords[1]})`;

  return (
    <div className={clsx("p-4 rounded-lg border", colorClasses[color])}>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-white">{title}</h4>
        <span className="text-xs px-2 py-0.5 bg-zkp-dark-border rounded text-gray-400">
          {commitment.point_type.toUpperCase()}
        </span>
      </div>
      
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400 w-8">x:</span>
          <code className="flex-1 text-xs text-gray-300 font-mono truncate">
            {commitment.point_coords[0].slice(0, 30)}...
          </code>
          <button
            onClick={() => onCopy(fullCoords, fieldId)}
            className="p-1 hover:bg-zkp-dark-border rounded transition-colors"
          >
            {copiedField === fieldId ? (
              <Check className="w-3 h-3 text-zkp-success" />
            ) : (
              <Copy className="w-3 h-3 text-gray-400" />
            )}
          </button>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400 w-8">y:</span>
          <code className="flex-1 text-xs text-gray-300 font-mono truncate">
            {commitment.point_coords[1].slice(0, 30)}...
          </code>
        </div>
        <div className="flex items-center gap-4 pt-2 border-t border-zkp-dark-border">
          <span className="text-xs text-gray-500">
            Type: {commitment.type}
          </span>
          <span className="text-xs text-gray-500">
            Degree: {commitment.metadata.degree}
          </span>
        </div>
      </div>
    </div>
  );
}

interface CopyableFieldProps {
  label: string;
  value: string;
  fullValue: string;
  onCopy: (text: string, field: string) => void;
  copiedField: string | null;
  fieldId: string;
}

function CopyableField({ label, value, fullValue, onCopy, copiedField, fieldId }: CopyableFieldProps) {
  const displayValue = value.length > 50 ? `${value.slice(0, 25)}...${value.slice(-25)}` : value;
  
  return (
    <div className="flex items-center gap-3 p-3 bg-zkp-dark-bg rounded-lg border border-zkp-dark-border">
      <span className="text-xs text-gray-400 w-32 flex-shrink-0">{label}</span>
      <code className="flex-1 text-xs text-gray-300 font-mono truncate">
        {displayValue}
      </code>
      <button
        onClick={() => onCopy(fullValue, fieldId)}
        className="p-1.5 hover:bg-zkp-dark-border rounded transition-colors flex-shrink-0"
      >
        {copiedField === fieldId ? (
          <Check className="w-4 h-4 text-zkp-success" />
        ) : (
          <Copy className="w-4 h-4 text-gray-400" />
        )}
      </button>
    </div>
  );
}

interface KZGProofCardProps {
  title: string;
  proof: KZGProof;
}

function KZGProofCard({ title, proof }: KZGProofCardProps) {
  const evalStr = String(proof.evaluation);
  const displayEval = evalStr.length > 30 ? `${evalStr.slice(0, 15)}...${evalStr.slice(-15)}` : evalStr;
  
  return (
    <div className="p-4 bg-zkp-dark-bg rounded-lg border border-zkp-dark-border">
      <h4 className="text-sm font-medium text-white mb-3">{title}</h4>
      
      <div className="space-y-2 text-xs">
        <div className="flex justify-between">
          <span className="text-gray-400">Evaluation:</span>
          <code className="text-gray-300 font-mono">{displayEval}</code>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Quotient Degree:</span>
          <span className="text-white">{proof.opening_proof.metadata.degree}</span>
        </div>
        <div className="pt-2 border-t border-zkp-dark-border">
          <p className="text-gray-500 mb-1">Opening Proof (G1):</p>
          <code className="text-xs text-gray-400 font-mono block truncate">
            ({proof.opening_proof.point_coords[0].slice(0, 20)}...)
          </code>
        </div>
      </div>
    </div>
  );
}
