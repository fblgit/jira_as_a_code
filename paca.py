import logging as log
import os
import random

import yaml
from jira import JIRA
import psycopg2

log.basicConfig(format='%(asctime)s %(message)s', level=log.INFO)

'''
================= LOCAL JIRA ============
docker volume create --name jiraVolume
docker run -v jiraVolume:/var/atlassian/application-data/jira --name="jira" -d -p 8080:8080 atlassian/jira-software

================== DATABASE =============

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

'''

DB_CFG = {
  'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
  'USER': os.environ.get('DB_USER', 'postgres'),
  'PASS': os.environ.get('DB_PASS', 'postgres'),
  'NAME': os.environ.get('DB_NAME', 'paca'),
  'PORT': int(os.environ.get('DB_PORT', 5432))
}

JIRA_CFG = {
  'HOST': os.environ.get('JIRA_HOST', 'http://127.0.0.1:8080'),
  'USER': os.environ.get('JIRA_USER', 'jirauser'),
  'PASS': os.environ.get('JIRA_PASS', 'jirapass'),
  'PROJECT': os.environ.get('JIRA_PROJECT', 'INFRA'),
  'FIELDS': {
    'TaskEpicName': 'customfield_10109',
    'EpicEpicName': 'customfield_10105'
  }
}

PAC_FILE = os.environ.get('PAC_FILE', 'pac.yaml')

class SQL():
  def __init__(self):
    self.db = psycopg2.connect(
      f"dbname={DB_CFG['NAME']} user={DB_CFG['USER']} \
        password={DB_CFG['PASS']} host={DB_CFG['HOST']} \
        port={DB_CFG['PORT']}")
    self.db.set_session(autocommit=True)
    self.sql = self.db.cursor()
  
  def check_epic(self, name):
    self.sql.execute('SELECT * FROM epic WHERE name=%s', (name,))
    if self.sql.fetchall():
      return True
    return False
  
  def check_task(self, name):
    self.sql.execute('SELECT * FROM task WHERE name=%s', (name,))
    if self.sql.fetchall():
      return True
    return False
  
  def check_quarter(self, epic):
    self.sql.execute('SELECT id FROM quarter WHERE epic=%s', (epic['jira_id'],))
    if self.sql.fetchall():
      return True
    return False
  
  def update_quarter(self, quarter_name, epic):
    self.sql.execute('UPDATE quarter SET id=%s WHERE epic=%s', (quarter_name, epic['jira_id']))
    return True

  def create_quarter_link(self, quarter_name, epic):
    self.sql.execute('SELECT * FROM quarter WHERE id=%s AND epic=%s', (quarter_name, epic['jira_id']))
    if self.sql.fetchall():
      return False
    self.sql.execute('INSERT INTO quarter VALUES( %s, %s)', (quarter_name, epic['jira_id']))
    return True

  def get_epic_links(self, epic):
    results = []
    self.sql.execute('SELECT task FROM links WHERE epic=%s', (epic['jira_id'],))
    for row in self.sql.fetchall():
      results.append(row[0])
    return results
  
  def create_link(self, epic, task):
    self.sql.execute('SELECT * FROM links WHERE epic=%s AND task=%s', (epic['jira_id'], task['jira_id']))
    if self.sql.fetchall():
      return False
    self.sql.execute('INSERT INTO links VALUES( %s, %s)', (epic['jira_id'], task['jira_id']))
    return True
  
  def get_epic_id(self, name):
    self.sql.execute('SELECT id FROM epic WHERE name=%s', (name,))
    for row in self.sql.fetchall():
      return row[0]
    return False

  def get_task_id(self, name):
    self.sql.execute('SELECT id FROM task WHERE name=%s', (name,))
    for row in self.sql.fetchall():
      return row[0]
    return False

  def task_is_gone(self, task):
    self.sql.execute('SELECT status FROM task WHERE id=%s', (task['jira_id'],))
    for row in self.sql.fetchall():
      if row[0] == 'GONE':
        return True
      else:
        print(f'whats this {row}')
    return False
  
  def set_gone_task(self, task):
    self.sql.execute('UPDATE task SET status=%s WHERE id=%s', ('GONE', task['jira_id']))
    return True

  def clean_db(self):
    self.sql.execute('TRUNCATE links')
    self.sql.execute('TRUNCATE epic')
    self.sql.execute('TRUNCATE task')
    self.sql.execute('TRUNCATE quarter')
    
  def create_epic(self, epic):
    EPIC_REQUIREMENTS = [
      'name',
      'estimation',
      'description',
      'jira_id'
    ]
    EPIC_DEFAULTS = {
      'status': 'NEW',
      'created_by': 'PACA'
    }
    for requirement in EPIC_REQUIREMENTS:
      if requirement not in epic:
        return False
    if self.check_epic(epic['name']):
      return False
    for default in EPIC_DEFAULTS:
      if default not in epic:
        epic[default] = EPIC_DEFAULTS[default]
    self.sql.execute('INSERT INTO epic VALUES( %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)',
     (
       epic['jira_id'],
       epic['name'],
       epic['estimation'],
       epic['description'],
       epic['status'],
       epic['created_by']
      )
    )
    return True
  
  def create_task(self, task):
    TASK_REQUIREMENTS = [
      'name',
      'estimation',
      'description',
      'jira_id'
    ]
    TASK_DEFAULTS = {
      'story_points': 0,
      'status': 'NEW',
      'created_by': 'PACA'
    }
    for requirement in TASK_REQUIREMENTS:
      if requirement not in task:
        return False
    if self.check_task(task['name']):
      return False
    for default in TASK_DEFAULTS:
      if default not in task:
        task[default] = TASK_DEFAULTS[default]
    self.sql.execute('INSERT INTO task VALUES( %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)',
     (
       task['jira_id'],
       task['name'],
       task['estimation'],
       task['description'],
       task['story_points'],
       task['status'],
       task['created_by']
      )
    )
    return True

  def get_all_tasks(self):
    results = []
    self.sql.execute('SELECT id FROM task')
    for row in self.sql.fetchall():
      results.append(row[0])
    return results

  def get_all_epics(self):
    results = []
    self.sql.execute('SELECT id FROM epic')
    for row in self.sql.fetchall():
      results.append(row[0])
    return results

  def get_task_status(self, task):
    self.sql.execute('SELECT status FROM task WHERE id=%s', (task['jira_id'],))
    for row in self.sql.fetchall():
      return row[0]
    return False
  
  def get_epic_status(self, epic):
    self.sql.execute('SELECT status FROM epic WHERE id=%s', (epic['jira_id'],))
    for row in self.sql.fetchall():
      return row[0]
    return False
  
  def update_task(self, task, field, new_value):
    self.sql.execute(f'UPDATE task SET {field}=%s WHERE id=%s', (new_value, task['jira_id']))
    return True

  def update_epic(self, epic, field, new_value):
    self.sql.execute(f'UPDATE epic SET {field}=%s WHERE id=%s', (new_value, epic['jira_id']))
    return True


class PACJIRA():
  def __init__(self):
    self.jira = JIRA(server=JIRA_CFG['HOST'], basic_auth=(JIRA_CFG['USER'], JIRA_CFG['PASS']))
    self.db = SQL()
    self.issues = {}
  
  def clean_issues(self):
    for task  in self.db.get_all_tasks():
      try:
        issue = self.jira.issue(task)
        issue.delete()
      except Exception as error:
        log.warn('[CLEAN] Failed to delete task >> %s >> %s', task, error)
    for epic in self.db.get_all_epics():
      try:
        issue = self.jira.issue(epic)
        issue.delete()
      except Exception as error:
        log.warn('[CLEAN] Failed to delete epic >> %s >> %s', task, error)
    return True

  def create_epic(self, epic):
    issue = self.jira.create_issue(
      project=JIRA_CFG['PROJECT'],
      summary=epic['name'],
      description=epic['description'],
      issuetype={'name': 'Epic'},
      customfield_10105=epic['name']
    )
    self.issues[issue.key] = issue
    return issue.key

  def create_task(self, task):
    issue = self.jira.create_issue(
      project=JIRA_CFG['PROJECT'],
      summary=task['name'],
      description=task['description'],
      issuetype={'name': 'Task'}
    )
    self.issues[issue.key] = issue
    return issue.key
  
  def link_epic_task(self, epic, task):
    if epic['jira_id'] not in self.issues:
      self.issues[epic['jira_id']] = self.jira.issue(epic['jira_id'])
    if task['jira_id'] not in self.issues:
      self.issues[task['jira_id']] = self.jira.issue(task['jira_id'])
    existing_links = self.issues[task['jira_id']].raw['fields'].get(JIRA_CFG['FIELDS']['TaskEpicName'], '')
    if existing_links == None or epic['jira_id'] not in existing_links:
      self.jira.add_issues_to_epic(epic['jira_id'], [task['jira_id']])
      return True
    return False
  
  def transition_issue(self, jira_id, transition_name):
    if transition_name == 'NEW':
      return True
    transition_id = self.jira.find_transitionid_by_name(jira_id, transition_name)
    if not transition_id:
      avail_transitions = [ x['name'] for x in self.jira.transitions(jira_id) ]
      log.error('[SET-TRANSITION] Failed Transitioning >> %s >> %s >> (available transitions: %s)', jira_id, transition_name, ', '.join(avail_transitions))
      return False
    log.debug('[SET-TRANSITION] Transitioning >> %s >> %s', jira_id, transition_name)
    self.jira.transition_issue(jira_id, transition_id)
    return True


class PAC():
  def __init__(self):
    self.pac = yaml.load(open(PAC_FILE, 'r').read(), Loader=yaml.Loader)
    self.db = SQL()
    self.jira = PACJIRA()

  def get_sop_template(self, name):
    if name in self.pac['sop_templates']:
      return self.pac['sop_templates'][name]
    return 'template-not-found'
  
  def clean_all(self):
    self.jira.clean_issues()
    self.db.clean_db()
    return True

  def get_quarters(self):
    results = []
    for quarter in self.pac['quarters']:
      results.append(quarter['name'])
    return results

  def process_epic(self, epic):
    log.info('[PROCESS-EPIC] Processing EPIC >> %s', epic['name'])
    if 'description' not in epic:
      epic['description'] = ''
    if 'sop_template' in epic:
      epic['description'] += '\n%s' % self.get_sop_template(epic['sop_template'])
    if not self.db.check_epic(epic['name']):
      log.debug('[CREATE-EPICS] Creating EPIC >> %s', epic['name'])
      epic['jira_id'] = self.jira.create_epic(epic)
      if not epic['jira_id']:
        log.error('[CREATE-EPICS] Error Creating EPIC JIRA >> %s', epic['name'])
        return False
      log.info('[CREATE-EPICS] Created EPIC JIRA >> %s << %s', epic['jira_id'], epic['name'])
      if not self.db.create_epic(epic):
        log.error('[CREATE-EPICS] Error Creating EPIC DB >> %s', epic['jira_id'])
        return False
      if 'status' in epic:
        self.jira.transition_issue(epic['jira_id'], epic['status'])
        self.db.update_epic(epic, 'status', epic['status'])
    else:
      log.debug('[CREATE-EPICS] Already Existing EPIC >> %s', epic['name'])
    epic['jira_id'] = self.db.get_epic_id(epic['name'])
    if epic.get('status', False):
      transition_name = epic['status']
      if transition_name != self.db.get_epic_status(epic):
        if self.jira.transition_issue(epic['jira_id'], transition_name):
          self.db.update_epic(epic, 'status', transition_name)
          log.info('[EPIC-STATUS] Updated Epic JIRA Status >> %s << %s', epic['jira_id'], transition_name)
    return epic['jira_id']

  def tasks_iterator(self, task_iterate):
    tasks = []
    for task_iteration in task_iterate:
      iterator = task_iteration['iterator']
      for iteration in task_iteration[iterator]:
        payload = {
          'name': task_iteration['name'].replace(f'%{iterator}%', iteration),
          'estimation': task_iteration['estimation'],
          'story_points': task_iteration['story_points'],
          'description': task_iteration['description'].replace(f'%{iterator}%', iteration)
        }
        for option in ['sop_template', 'status']:
          if option in task_iteration:
            payload[option] = task_iteration[option]
        tasks.append(payload)
    return tasks

  def process_task(self, epic, task):
    log.info('[PROCESS-TASK] Processing Task >> %s', task['name'])
    if 'description' not in task:
      task['description'] = ''
    if 'sop_template' in task:
      task['description'] += '\n%s' % self.get_sop_template(task['sop_template'])
    if not self.db.check_task(task['name']):
      log.debug('[CREATE-TASKS] Creating TASK >> %s', task['name'])
      task['jira_id'] = self.jira.create_task(task)
      if not task['jira_id']:
        log.error('[CREATE-TASK] Error Creating TASK JIRA >> %s', task['name'])
        return False
      log.info('[CREATE-TASKS] Created TASK JIRA >> %s << %s', task['jira_id'], task['name'])
      if not self.db.create_task(task):
        log.error('[CREATE-TASKS] Error Creating TASK DB >> %s', epic['jira_id'])
        return False
      if not self.db.create_link(epic, task) or not self.jira.link_epic_task(epic, task):
        log.error('[CREATE-LINK] Error Linking EPIC >> %s << %s TASK', epic['jira_id'], task['jira_id'])
        return False
      log.info('[CREATE-LINK] Linked JIRA EPIC >> %s << %s TASK', epic['jira_id'], task['jira_id'])
      transition_name = task.get('status', epic.get('task_status', False))
      if transition_name:
        self.jira.transition_issue(task['jira_id'], transition_name)
        self.db.update_task(task, 'status', transition_name)
        db_status = self.db.get_task_status(task)
        log.info('[NEW-TRANSITION] Transitioned New Task JIRA >> %s << %s (db: %s)', task['jira_id'], transition_name, db_status)
    else:
      log.debug('[CREATE-TASKS] Already Existing TASK >> %s', epic['name'])
    task['jira_id'] = self.db.get_task_id(task['name'])
    if epic.get('task_status', False):
      transition_name = epic['task_status']
      if task.get('status', False):
        transition_name = task['status']
      if transition_name != self.db.get_task_status(task):
        if self.jira.transition_issue(task['jira_id'], transition_name):
          self.db.update_task(task, 'status', transition_name)
          log.info('[TASK-STATUS] Updated Task JIRA Status >> %s << %s', task['jira_id'], transition_name)
    return task['jira_id']

  def process_quarter(self, quarter_name):
    for quarter in self.pac['quarters']:
      if quarter['name'] == quarter_name:
        log.info('[PROCESS-QUARTER] Processing Epics for Quarter >> %s', quarter_name)
        for epic in quarter['epics']:
          epic['jira_id'] = self.process_epic(epic)
          if not epic['jira_id']:
            continue
          # Ensure Quarter Links
          if self.db.check_quarter(epic):
            # Ensure Epic is in the right Quarter, there is scenarios
            # where Epic can shift to different quarters due to planning
            self.db.update_quarter(quarter_name, epic)
          else:
            self.db.create_quarter_link(quarter_name, epic)
            log.info('[QUARTER-EPIC] Linked Quarter >> %s << %s EPIC', quarter_name, epic['jira_id'])
          epic['task_ids'] = []
          if epic.get('status', False):
            if self.db.get_epic_status(epic) != epic['status']:
              if self.jira.transition_issue(epic['jira_id'], epic['status']):
                self.db.update_epic(epic, 'status', epic['status'])
                log.info('[EPIC-STATUS] Updated Epic JIRA Status >> %s << %s', epic['jira_id'], epic['status'])
          if epic.get('tasks_iterate', False):
            tasks_iteration = self.tasks_iterator(epic['tasks_iterate'])
            if 'tasks' not in epic:
              epic['tasks'] = tasks_iteration
            else:
              epic['tasks'] = epic['tasks'] + tasks_iteration
          if 'tasks' in epic:
            # process tasks
            log.debug('[CREATE-TASKS] Processing Tasks for >> %s', epic['name'])
            for task in epic['tasks']:
                if 'status' not in task and 'task_status' in epic:
                  task['status'] = epic['task_status']
                task['jira_id'] = self.process_task(epic, task)
                if not task['jira_id']:
                  continue
                epic['task_ids'].append(task['jira_id'])
                # Here we should update the status, assignee, etc..
                if task.get('status', False):
                  if self.db.get_task_status(task) != task['status']:
                    if self.jira.transition_issue(task['jira_id'], task['status']):
                      self.db.update_task(task, 'status', task['status'])
                      log.info('[TASK-STATUS] Updated Task JIRA Status >> %s << %s', task['jira_id'], task['status'])
          for task_id in self.db.get_epic_links(epic):
            if task_id not in epic['task_ids']:
              if not self.db.task_is_gone(task={'jira_id': task_id}):
                log.info('[EPIC-CONSISTENCY] Task JIRA >> %s << GONE FROM EPIC >> %s', task_id, epic['jira_id'])
                self.db.set_gone_task(task={'jira_id': task_id})
    # In a next version, there should be a mechanism to reconciliate whats happening on JIRA
    # back to the PACA database, in this way there is a possibility of creating reports
    # and realtime dashboards to represent the progress of OKR during a quarter
    return True


if __name__ == '__main__':
  pac = PAC()
  # for dev:
  # you can uncomment the clean_all and it will delete all jira issues
  # as well as all database entries, good for testing.
  #
  # pac.clean_all()
  for quarter in pac.get_quarters():
    pac.process_quarter(quarter)

