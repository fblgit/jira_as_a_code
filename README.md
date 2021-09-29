# Jira as a Code YAML (PACA)
PACA - Project as Code Assistant

tired of wasting time with jira.. making epics, tasks, links, this and that... transition to backlog, to do, whatever...

With PACA you can avoid a lot of non-sense-wasting-time with JIRA and drive the sprints, quarters, planning, or a project thru a YAML.
This is how `pac.yaml` looks

```
sop_templates:
  cluster_migration_steps: |
    Each cluster has to be performed according this process:
    1 - Creation of new infrastructure via Terraform
    2 - Cleanup old resources from previous cluster

    DOD: Cleanup task has been completed.
  argo_update: |
    1 - argo step 1
    2 - argo step 2
  mesh_rollout: |
    1 - mesh step 1
    2 - mesh step 2
    3 - mesh step 3

    Validation: you should see lorem ipsum

quarters:
  - name: 2021_Q4
    epics:
      - name: Upgrade Fleet to ArgoCD v2.1.1
        estimation: 8w
        description: |
          As part of our LifeCycle, we need to upgrade our ArgoCD to v2.1.1
        sop_template: argo_update
        task_status: Backlog
        status: In Progress
        tasks_iterate:
          - name: ArgoCD Upgrade on %CLUSTER% to v2.1.1
            iterator: CLUSTER
            CLUSTER:
              - prod-cluster-1
              - prod-cluster-2
              - prod-cluster-3
            estimation: 1d
            story_points: 10
            sop_template: argo_update
            description: As part of our LifeCycle, we need to upgrade %METACLUSTER% ArgoCD to v2.1.1
        tasks:
          - name: ArgoCD Fleet Sync
            sop_template: argo_update
            story_points: 15
            estimation: 4h
            status: Selected for Development
            description: Sync ArgoCD in the Fleet
      - name: Upgrades K8s Fleet to v1.21
        estimation: 8w
        description: |
          As part of our LifeCycle, we need to upgrade our kubernetes clusters to v1.21
        sop_template: cluster_migration_steps
        task_status: Backlog
        status: In Progress
        tasks:
          - name: K8s - Migration - v1.21 prod-cluster-1 cluster
            estimation: 3d
            story_points: 10
            sop_template: cluster_migration_steps
            description: As part of our LifeCycle, we need to upgrade prod-cluster-1 kubernetes cluster to v1.21
          - name: K8s - Migration - v1.21 prod-cluster-2 cluster
            estimation: 3d
            story_points: 10
            sop_template: cluster_migration_steps
            description: As part of our LifeCycle, we need to upgrade prod-cluster-2 kubernetes cluster to v1.21
            status: Selected for Development
      - name: Rollout Service Mesh on Kubernetes Fleet
        estimation: 2w
        description: |
          Enable Traefik on the cluster
          This has to be performed in a specific order:
          1 - Staging
          2 - Production Fleet
            prod-cluster-1
            prod-cluster-2
            << COOLDOWN >> 3d
            .. the rest of clusters ..
        tasks:
          - name: K8s - ServiceMesh - Staging Clusters
            estimation: 2d
            story_points: 20
            sop_template: mesh_rollout
          - name: K8s - ServiceMesh - Prod Clusters
            estimation: 5d
            story_points: 40
            sop_template: mesh_rollout
```

There are features such as:

* tasks_iterate
Allows you to iterate over a list, that can be used as well to replace the name and description, and create as many jira tasks as it requires with minimum effort.

* task_status
Define the default status for the tasks of an epic, in this way you can have epics and their tasks on backlog then you can transition it into ToDo or whatever at light-speed.

* sop_template
Define templates that can be reused as descriptions of the tasks. They either become the whole description or they are appended to a description, thats up to you.

* epics
Declare EPICs and inside their tasks, they will automatically get linked.

* quarters
You can create many, and you can move Epics from one to another.. PACA will take care of the changes.

Since its declarative and overall produces a model, you can simply interpolate up-down some of the values within the epic->tasks and save time.

## TODO
- Add a mechanism to consolidate JIRA>PACA information so you can use the PACA DB to create dashboards, reports, etc.
- Email or Slack (similar) integration to let the assignee to know that he is getting out of time or already out of time on a task
- Assign a task or a whole epic to a user/s
- some other fancy stuff that would make my life easier..

## ALREADY KNOW
- Yah you can make all this and much more with jira, but not as fast as this... yah you can make reports or whatever, with plugins or any other complicated ways of doing it.
- No, ABSOLUTELY you CANNOT make a long quarter planning (epic, tasks, status, links, etc) click by click faster than PACA..
- Yes, YAML to structure the planning is much faster than click by click on Jira
- Yes, I could put testcases or whatever... but I have no time and yet this is a very small project. But if u want, throw a PR for it or any other improvement.

## CONTRIBUTING

Talk is free, commits are not. Waiting for your PR.
