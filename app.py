import csv
import io
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, make_response

app = Flask(__name__)

PROJECTS_FILE = 'projects.csv'
TASKS_FILE = 'tasks.csv'
USERS_FILE = 'users.csv'
AUDIT_FILE = 'audit.csv'


def read_csv(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def write_csv(filepath, fieldnames, data):
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def get_next_id(filepath):
    data = read_csv(filepath)
    if not data:
        return 1
    return max(int(row['id']) for row in data) + 1


def get_project_progress(project_id):
    tasks = read_csv(TASKS_FILE)
    project_tasks = [t for t in tasks if int(t['project_id']) == project_id]
    if not project_tasks:
        return 0
    completed = sum(1 for t in project_tasks if t['status'] == 'Completed')
    return round((completed / len(project_tasks)) * 100)


def get_task_count(project_id):
    tasks = read_csv(TASKS_FILE)
    return sum(1 for t in tasks if int(t['project_id']) == project_id)


def get_users():
    return read_csv(USERS_FILE)


def add_user(name):
    if not name:
        return
    users = read_csv(USERS_FILE)
    if any(u['name'] == name for u in users):
        return
    new_id = get_next_id(USERS_FILE)
    users.append({'id': str(new_id), 'name': name})
    write_csv(USERS_FILE, ['id', 'name'], users)


def add_audit_log(task_id, task_name, field_changed, old_value, new_value, changed_by):
    audit = read_csv(AUDIT_FILE)
    new_id = get_next_id(AUDIT_FILE)
    audit.append({
        'id': str(new_id),
        'task_id': str(task_id),
        'task_name': task_name,
        'field_changed': field_changed,
        'old_value': old_value,
        'new_value': new_value,
        'changed_by': changed_by,
        'changed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    write_csv(AUDIT_FILE, ['id', 'task_id', 'task_name', 'field_changed', 'old_value', 'new_value', 'changed_by', 'changed_at'], audit)


def get_task_audit_history(task_id):
    audit = read_csv(AUDIT_FILE)
    return [a for a in audit if int(a['task_id']) == task_id]


@app.route('/')
def index():
    projects = read_csv(PROJECTS_FILE)
    for p in projects:
        p['progress'] = get_project_progress(int(p['id']))
        p['task_count'] = get_task_count(int(p['id']))
    return render_template('index.html', projects=projects)


@app.route('/project/<int:project_id>')
def project(project_id):
    projects = read_csv(PROJECTS_FILE)
    project = next((p for p in projects if int(p['id']) == project_id), None)
    if not project:
        return "Project not found", 404
    
    tasks = read_csv(TASKS_FILE)
    project_tasks = [t for t in tasks if int(t['project_id']) == project_id]
    project['progress'] = get_project_progress(project_id)
    users = get_users()
    
    return render_template('project.html', project=project, tasks=project_tasks, users=users)


@app.route('/add_project', methods=['POST'])
def add_project():
    name = request.form.get('name')
    description = request.form.get('description')
    
    if name:
        projects = read_csv(PROJECTS_FILE)
        new_id = get_next_id(PROJECTS_FILE)
        new_project = {
            'id': str(new_id),
            'name': name,
            'description': description or '',
            'created_at': datetime.now().strftime('%Y-%m-%d')
        }
        projects.append(new_project)
        write_csv(PROJECTS_FILE, ['id', 'name', 'description', 'created_at'], projects)
    
    return redirect(url_for('index'))


@app.route('/add_user', methods=['POST'])
def add_user_route():
    name = request.form.get('name')
    project_id = request.form.get('project_id')
    add_user(name)
    return redirect(url_for('project', project_id=project_id))


@app.route('/add_task/<int:project_id>', methods=['POST'])
def add_task(project_id):
    name = request.form.get('name')
    description = request.form.get('description')
    assignee = request.form.get('assignee')
    notes = request.form.get('notes')
    updated_date = request.form.get('updated_date') or datetime.now().strftime('%Y-%m-%d')
    changed_by = request.form.get('changed_by', 'System')
    
    if name:
        tasks = read_csv(TASKS_FILE)
        new_id = get_next_id(TASKS_FILE)
        new_task = {
            'id': str(new_id),
            'project_id': str(project_id),
            'name': name,
            'description': description or '',
            'status': 'Not Started',
            'assignee': assignee or '',
            'notes': notes or '',
            'updated_date': updated_date,
            'created_at': datetime.now().strftime('%Y-%m-%d')
        }
        tasks.append(new_task)
        write_csv(TASKS_FILE, ['id', 'project_id', 'name', 'description', 'status', 'assignee', 'notes', 'updated_date', 'created_at'], tasks)
        
        add_audit_log(new_id, name, 'Created', '', 'Task created', changed_by)
    
    return redirect(url_for('project', project_id=project_id))


@app.route('/update_task/<int:task_id>', methods=['POST'])
def update_task(task_id):
    new_status = request.form.get('status')
    assignee = request.form.get('assignee')
    notes = request.form.get('notes')
    updated_date = request.form.get('updated_date')
    changed_by = request.form.get('changed_by', 'Unknown')
    
    tasks = read_csv(TASKS_FILE)
    project_id = None
    for task in tasks:
        if int(task['id']) == task_id:
            if task['status'] != new_status:
                add_audit_log(task_id, task['name'], 'Status', task['status'], new_status, changed_by)
            if task['assignee'] != (assignee or ''):
                add_audit_log(task_id, task['name'], 'Assignee', task['assignee'], assignee or '', changed_by)
            if task['notes'] != (notes or ''):
                add_audit_log(task_id, task['name'], 'Notes', task['notes'], notes or '', changed_by)
            
            task['status'] = new_status
            task['assignee'] = assignee or ''
            task['notes'] = notes or ''
            if updated_date:
                task['updated_date'] = updated_date
            project_id = task['project_id']
            break
    
    if project_id:
        write_csv(TASKS_FILE, ['id', 'project_id', 'name', 'description', 'status', 'assignee', 'notes', 'updated_date', 'created_at'], tasks)
        return redirect(url_for('project', project_id=project_id))
    
    return "Task not found", 404


@app.route('/task_audit/<int:task_id>')
def task_audit(task_id):
    tasks = read_csv(TASKS_FILE)
    task = next((t for t in tasks if int(t['id']) == task_id), None)
    if not task:
        return "Task not found", 404
    
    audit_history = get_task_audit_history(task_id)
    return render_template('audit.html', task=task, audit_history=audit_history)


@app.route('/export_project/<int:project_id>/csv')
def export_project_csv(project_id):
    projects = read_csv(PROJECTS_FILE)
    project = next((p for p in projects if int(p['id']) == project_id), None)
    if not project:
        return "Project not found", 404
    
    tasks = read_csv(TASKS_FILE)
    project_tasks = [t for t in tasks if int(t['project_id']) == project_id]
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Description', 'Status', 'Assignee', 'Notes', 'Updated Date', 'Created At'])
    for task in project_tasks:
        writer.writerow([
            task['id'],
            task['name'],
            task['description'],
            task['status'],
            task['assignee'],
            task['notes'],
            task['updated_date'],
            task['created_at']
        ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename="{project["name"]}_tasks.csv"'
    
    return response


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5000)
