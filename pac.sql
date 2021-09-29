CREATE TABLE "quarter" (
  "id" varchar,
  "epic" varchar
);

CREATE TABLE "task" (
  "id" varchar PRIMARY KEY,
  "name" varchar,
  "estimation" varchar,
  "description" varchar,
  "story_points" int,
  "status" varchar,
  "created_by" varchar,
  "creation" timestamp
);

CREATE TABLE "epic" (
  "id" varchar PRIMARY KEY,
  "name" varchar,
  "estimation" varchar,
  "description" varchar,
  "status" varchar,
  "created_by" varchar,
  "creation" timestamp
);

CREATE TABLE "links" (
  "epic" varchar,
  "task" varchar
);

CREATE TABLE "assigned" (
  "task" varchar,
  "infra_user" varchar
);

CREATE TABLE "comments" (
  "id" varchar,
  "content" varchar,
  "created_by" varchar,
  "creation" timestamp
);
