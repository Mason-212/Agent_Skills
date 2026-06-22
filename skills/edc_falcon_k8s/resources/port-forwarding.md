# Port Forwarding

Instructions for port-forwarding to services in a Falcon-managed Kubernetes cluster.

## Prerequisites

kubectl must be configured and pointing to the correct namespace. If not, run the main falcon-k8s workflow first (Steps 1–9 in SKILL.md).

## Workflow

### Step 1: Ask the User for Service Name

Ask the user which service they want to port-forward to:

> "Which service do you want to port-forward to?"

### Step 2: Check Available Ports

Once the user provides the service name, inspect its ports:

```bash
kubectl get svc <service-name> -o jsonpath='{.spec.ports[*]}'
```

Or for a more readable view:

```bash
kubectl get svc <service-name>
```

Present the available ports to the user and ask which one they want to forward:

> "Service `<service-name>` exposes the following ports:"
> - `<port-name>`: `<port>` → `<targetPort>`
> - ...
>
> "Which port would you like to forward, and to which local port?"

If the user doesn't specify a local port, default to using the same port number as the remote.

### Step 3: Port Forward

```bash
kubectl port-forward svc/<service-name> <local-port>:<remote-port>
```

## Discovering Available Services

If the user doesn't know the service name, list services in the current namespace:

```bash
kubectl get svc
```

Present the list and let them pick.

## Common Options

Forward on a specific local address (e.g., to allow access from other machines):

> **Warning:** Binding to `0.0.0.0` exposes the forwarded port to all network interfaces. Only use this when you specifically need access from other machines and understand that anyone on your network can reach the service.

```bash
kubectl port-forward svc/<service-name> --address 0.0.0.0 <local-port>:<remote-port>
```

Forward multiple ports at once:

```bash
kubectl port-forward svc/<service-name> <local-port1>:<remote-port1> <local-port2>:<remote-port2>
```

## Running in Background

To keep the port-forward running while doing other work:

```bash
kubectl port-forward svc/<service-name> <local-port>:<remote-port> &
```

To stop it later:

```bash
kill %1
```

Or find the process:

```bash
ps aux | grep port-forward
```

## Troubleshooting

### "error: unable to forward port because pod is not running"
The service's backing pods may not be healthy. Check:

```bash
kubectl get pods
kubectl describe svc <service-name>
```

### Connection refused on localhost
- Verify the port-forward is still running (it can timeout or disconnect)
- Verify you're using the correct local port
- Re-run the port-forward command

### "unable to find a pod matching the label selector"
The service may have no endpoints. Check:

```bash
kubectl get endpoints <service-name>
```
