# IAM Design — Clickstream Real-Time Data Platform

This document defines the **Identity and Access Management (IAM) design** for the clickstream real-time data platform.

It acts as the **authorization contract** between AWS services, human users, and automated systems involved in the platform.

---

## 1. Design Principles

The IAM setup follows strict principles to ensure correctness, safety, and production realism:

* **Least privilege by default**
* **Clear separation of control plane and data plane**
* **No shared identities across components**
* **No long-lived credentials for services**
* **Human access separated from system access**

---

## 2. Actors and Identity Types

The platform interacts with AWS using the following actors:

### 2.1 Human Actors

* Project owner / developer (IAM User)

### 2.2 System Actors

* Amazon EMR (control plane)
* EC2 instances inside EMR (Spark driver & executors)
* Future: Airflow (orchestrator)
* Future: CI/CD pipeline (GitHub Actions via OIDC)

---

## 3. IAM Roles Overview

| Role Name                     | Type         | Used By       | Purpose                          |
| ----------------------------- | ------------ | ------------- | -------------------------------- |
| DataPlatform-EMR-EC2-Role     | EC2 Role     | Spark runtime | Data-plane access to S3 and logs |
| DataPlatform-EMR-Service-Role | Service Role | EMR service   | Cluster lifecycle management     |
| DataPlatform-Admin-User       | IAM User     | Human         | Infrastructure setup and control |

---

## 4. Human Access Model

### 4.1 IAM Admin User

A single IAM user is created for human access:

* **Access type**: Console login
* **Permissions**: `AdministratorAccess` (temporary for learning phase)
* **MFA**: Mandatory

Root user is secured with MFA and not used for daily operations.

---

## 5. EMR Runtime Identity (Data Plane)

### Role: `DataPlatform-EMR-EC2-Role`

This role is assumed by **EC2 instances created as part of an EMR cluster**.

These instances execute:

* Spark driver process
* Spark executor JVMs

#### Trust Relationship

* Trusted entity: `ec2.amazonaws.com`

#### Attached Policies

1. **AmazonElasticMapReduceforEC2Role** (AWS managed)

   * Required for EMR worker node operation

2. **SparkS3DataAccess** (Custom inline policy)

   * Read/write access to platform S3 buckets
   * Explicit protection of Spark checkpoints

#### S3 Access Scope

| Bucket                        | Access       | Notes                   |
| ----------------------------- | ------------ | ----------------------- |
| clickstream-raw-<env>         | Read / Write | Immutable event storage |
| clickstream-curated-<env>     | Read / Write | Aggregated datasets     |
| clickstream-checkpoints-<env> | Read / Write | Streaming state         |

**Explicit Deny:** deletion of any object under the checkpoints bucket.

#### Rationale

Spark requires:

* Durable checkpoint writes for recovery
* Ability to re-read raw data
* Strict protection against state loss

---

## 6. EMR Service Identity (Control Plane)

### Role: `DataPlatform-EMR-Service-Role`

This role is assumed by the **Amazon EMR service itself**.

#### Trust Relationship

* Trusted entity: `elasticmapreduce.amazonaws.com`

#### Attached Policy

* **AmazonEMRServicePolicy_v2** (AWS managed)

#### Responsibilities

* Create and terminate EMR clusters
* Attach instance roles and security groups
* Interact with EC2, Auto Scaling, and CloudWatch

#### Restrictions

* No direct access to S3 data buckets
* No permission to run Spark logic

---

## 7. Separation of Responsibilities

| Area                 | Responsible Identity         |
| -------------------- | ---------------------------- |
| Data correctness     | Spark runtime (EMR EC2 role) |
| State and recovery   | Spark + S3 checkpoints       |
| Cluster lifecycle    | EMR service role             |
| Infrastructure setup | IAM admin user               |

No IAM role crosses these boundaries.

---

## 8. Security Safeguards

* Root user protected with MFA and unused
* No access keys for root user
* All services use IAM roles (no static secrets)
* Checkpoint deletion explicitly denied

---

## 9. Future Extensions (Planned)

The following IAM roles will be added as the platform evolves:

* **Airflow Execution Role**

  * EMR step submission
  * Artifact access
  * No data-plane access

* **GitHub Actions Deployment Role (OIDC)**

  * Push artifacts and images
  * No runtime permissions

These will follow the same design principles documented here.

---

## 10. Design Status

* ✅ Human access configured
* ✅ EMR runtime IAM role implemented
* ✅ EMR service IAM role implemented
* ⏳ Airflow and CI/CD roles pending

This document represents the **authoritative IAM reference** for the project.
