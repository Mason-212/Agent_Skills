# Integration Testing in Strata Pipelines

Integration tests run in the `integration-test` stage, after build and package but before publish.

## Docker Compose Managed Steps

Strata provides `docker-compose-up` and `docker-compose-down` managed steps for the `integration-test` stage.

### docker-compose-up Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `background` | `true` | When `false`, runs in foreground with `--abort-on-container-exit` |
| `docker-compose-files` | `[docker-compose.yml]` | List of compose YAML files |
| `environment` | `{}` | Additional environment variables for compose |
| `output-logs` | `true` | Output container logs (background mode) |
| `output-process-list` | `true` | Periodically runs `docker-compose ps -a` |
| `process-list-frequency` | `30` | Seconds between process list output |
| `project-name` | `src` | Custom project name; controls network name prefix |

## Key Environment Variables

- **`$$ITEST_IMAGE_TAG`** -- Tag applied to images built in the `package` stage; use in compose files or docker commands.
- **`BUILD_WORKSPACE`** -- Mount path for the build workspace (do NOT use `pwd` or `.`).
- **`BUILD_AGENT_IP_ADDR`** -- Use instead of `localhost` to reach exposed container ports from custom steps.

## Pattern 1: Background Docker Compose with Custom Test Step

Docker Compose starts services in the background; a custom step runs the tests. Use `project-name` to get a predictable network name.

docker-compose.yml:
```yaml
version: "2.0"
services:
  localstack:
    image: docker.repo.local.sfdc.net/sfci/3pp/3pp/docker.io/localstack/localstack:0.13.2
    environment:
      AWS_DEFAULT_REGION: us-west-2
      SERVICES: dynamodb,s3
      HOSTNAME: localstack
      HOSTNAME_EXTERNAL: localstack
      EDGE_PORT: 4566
    ports:
      - "4566:4566"
    networks:
      default:
        aliases:
          - localstack-network
  web:
    image: docker.repo.local.sfdc.net/sfci/salesforce-internal/example-nodejs-int-tests:$$ITEST_IMAGE_TAG
    depends_on:
      - localstack
    ports:
      - "8000:8000"
    environment:
      AWS_REGION: us-west-2
      AWS_ACCESS_KEY_ID: "fake"
      AWS_SECRET_ACCESS_KEY: "fake"
      AWS_DYNAMODB_ENDPOINT: http://localstack:4566
```

.strata.yml:
```yaml
stages:
  build:
    - npm-setup
    - step:
        name: install-dependencies
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9_nodejs18
        commands:
          - npm install
  package:
    - docker-build
  integration-test:
    - docker-compose-up:
        project-name: example
    - step:
        name: run-int-tests
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9_docker/docker
        environment:
          - name: BUILD_AGENT_IP_ADDR
          - name: BUILD_WORKSPACE
          - name: ITEST_IMAGE_TAG
        commands:
          - docker run --network example_default -v $BUILD_WORKSPACE/scripts:/scripts -e WEB_HOST=web -e LOCALSTACK_HOST=localstack docker.repo.local.sfdc.net/sfci/salesforce-internal/example-nodejs-int-tests:$ITEST_IMAGE_TAG /scripts/run_int_tests.sh
    - docker-compose-down
```

## Pattern 2: Foreground Docker Compose (Pure Compose)

Run compose in the foreground with `background: false`. The exit code of the first container to finish determines success/failure. Use `docker-compose-files` to layer a test service on top of your base compose file.

docker-compose-int-tests.yml:
```yaml
version: "2.0"
services:
  int-tests:
    image: docker.repo.local.sfdc.net/sfci/salesforce-internal/example-nodejs-int-tests:$$ITEST_IMAGE_TAG
    depends_on:
      - localstack
      - web
    volumes:
      - ${BUILD_WORKSPACE:-.}/scripts:/scripts
    environment:
      WEB_HOST: web
      LOCALSTACK_HOST: localstack
    entrypoint: /scripts/run_int_tests.sh
```

.strata.yml:
```yaml
stages:
  integration-test:
    - docker-compose-up:
        background: false
        docker-compose-files:
          - docker-compose.yml
          - docker-compose-int-tests.yml
```

## Pattern 3: Manual Docker Steps (No Compose)

Use a custom step with `docker run` commands directly. Requires `workspace-mount-point` and the docker CLI image.

.strata.yml:
```yaml
stages:
  integration-test:
    - step:
        name: run-int-tests
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9_docker/docker
        workspace-mount-point: $$BUILD_WORKSPACE
        environment:
          - name: ITEST_IMAGE_TAG
          - name: BUILD_AGENT_IP_ADDR
          - name: BUILD_WORKSPACE
        commands:
          - $BUILD_WORKSPACE/scripts/run_docker_int_tests.sh
```

The shell script starts containers with `docker run -d`, uses `trap` to stop them on exit, and connects via `BUILD_AGENT_IP_ADDR`.

## LocalStack for AWS Service Emulation

Use the approved LocalStack image to emulate AWS services (DynamoDB, S3, SQS, etc.) during integration tests.

```yaml
localstack:
  image: docker.repo.local.sfdc.net/sfci/3pp/3pp/docker.io/localstack/localstack:0.13.2
  environment:
    AWS_DEFAULT_REGION: us-west-2
    SERVICES: dynamodb,s3,sqs
    HOSTNAME: localstack
    HOSTNAME_EXTERNAL: localstack
    EDGE_PORT: 4566
  ports:
    - "4566:4566"
```

Connect application services to LocalStack using the internal Docker network hostname (e.g., `http://localstack:4566`). Use fake AWS credentials (`AWS_ACCESS_KEY_ID: "fake"`, `AWS_SECRET_ACCESS_KEY: "fake"`).

Available versions are listed in the 3PP `images.yaml`. Check LocalStack release notes for feature coverage per version.
