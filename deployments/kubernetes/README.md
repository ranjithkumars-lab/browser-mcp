# Kubernetes Deployment

The `manifests.yaml` file contains a ConfigMap, Deployment, and Service for a
basic single-namespace deployment.

## Deploy

```bash
kubectl apply -f deployments/kubernetes/manifests.yaml
```

## Secrets

Create a secret for the API key when authentication is enabled:

```bash
kubectl create secret generic enterprise-mcp-secrets \
  --from-literal=api-key=<your-api-key>
```

## Tuning

- Adjust `replicas` for scale.
- Provide a production image reference instead of the placeholder
  `ghcr.io/your-org/enterprise-mcp-server:latest`.
- Terminate TLS at the ingress (e.g. an Ingress resource or service mesh).
