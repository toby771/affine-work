import torch
from toploc import build_proofs_base64, verify_proofs_base64

prefill = [torch.randn(5, 16, dtype=torch.bfloat16)]
generate = [torch.randn(16, dtype=torch.bfloat16) for _ in range(16)]
activations = prefill + generate

proof = build_proofs_base64(
    activations,
    decode_batching_size=3,
    topk=4,
    skip_prefill=False
)

print(proof)

activations = [i * 1.01 for i in activations]

# Verify
results = verify_proofs_base64(
    activations, 
    proof, 
    decode_batching_size=3, 
    topk=4, 
    skip_prefill=False
)
print(*results, sep="\n")