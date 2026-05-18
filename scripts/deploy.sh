#!/bin/bash
set -e

NAMESPACE="${NAMESPACE:-default}"
BACKEND_IMAGE="${BACKEND_IMAGE:-agentic-crm-backend:latest}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-agentic-crm-frontend:latest}"

echo "=== Deploying Agentic CRM to Kubernetes ==="
echo "Namespace: $NAMESPACE"
echo "Backend image: $BACKEND_IMAGE"
echo "Frontend image: $FRONTEND_IMAGE"

kubectl config use-context "$KUBECTX" 2>/dev/null || true

kubectl apply -f kubernetes/base/configmap.yaml -n "$NAMESPACE"
kubectl apply -f kubernetes/base/secret.yaml -n "$NAMESPACE" || true
kubectl apply -f kubernetes/base/pvc.yaml -n "$NAMESPACE"

kubectl apply -f kubernetes/base/ -n "$NAMESPACE"

kubectl set image deployment/backend backend="$BACKEND_IMAGE" -n "$NAMESPACE"
kubectl set image deployment/frontend frontend="$FRONTEND_IMAGE" -n "$NAMESPACE"
kubectl set image deployment/celery-worker celery-worker="$BACKEND_IMAGE" -n "$NAMESPACE"
kubectl set image deployment/celery-beat celery-beat="$BACKEND_IMAGE" -n "$NAMESPACE"

echo "=== Waiting for rollout ==="
kubectl rollout status deployment/backend -n "$NAMESPACE" --timeout=300s || echo "Backend rollout timed out"
kubectl rollout status deployment/frontend -n "$NAMESPACE" --timeout=300s || echo "Frontend rollout timed out"
kubectl rollout status deployment/celery-worker -n "$NAMESPACE" --timeout=300s || echo "Celery worker rollout timed out"
kubectl rollout status deployment/celery-beat -n "$NAMESPACE" --timeout=300s || echo "Celery beat rollout timed out"

echo "=== Checking pod status ==="
kubectl get pods -n "$NAMESPACE"

echo "=== Deployment complete ==="

echo "=== Running health checks ==="
sleep 10
BACKEND_POD=$(kubectl get pods -n "$NAMESPACE" -l app=agentic-crm,component=backend -o jsonpath='{.items[0].metadata.name}')
if kubectl exec "$BACKEND_POD" -n "$NAMESPACE" -- curl -sf http://localhost:8000/health; then
    echo "Backend health check: PASSED"
else
    echo "Backend health check: FAILED"
fi

echo "=== Done ==="