import pytest
import os
import csv
import tempfile
from datetime import datetime
from app import app, PROJECTS_FILE, TASKS_FILE, USERS_FILE, AUDIT_FILE, read_csv, write_csv, get_next_id, get_project_progress, get_task_count, get_users, add_user, add_audit_log, get_task_audit_history


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def temp_csv_files(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        projects_path = os.path.join(tmpdir, 'projects.csv')
        tasks_path = os.path.join(tmpdir, 'tasks.csv')
        users_path = os.path.join(tmpdir, 'users.csv')
        audit_path = os.path.join(tmpdir, 'audit.csv')
        
        monkeypatch.setattr('app.PROJECTS_FILE', projects_path)
        monkeypatch.setattr('app.TASKS_FILE', tasks_path)
        monkeypatch.setattr('app.USERS_FILE', users_path)
        monkeypatch.setattr('app.AUDIT_FILE', audit_path)
        
        write_csv(projects_path, ['id', 'name', 'description', 'created_at'], [
            {'id': '1', 'name': 'Test Project', 'description': 'Test description', 'created_at': '2026-03-01'}
        ])
        write_csv(tasks_path, ['id', 'project_id', 'name', 'description', 'status', 'assignee', 'notes', 'updated_date', 'created_at'], [
            {'id': '1', 'project_id': '1', 'name': 'Task 1', 'description': 'Desc 1', 'status': 'Not Started', 'assignee': '', 'notes': '', 'updated_date': '2026-03-01', 'created_at': '2026-03-01'},
            {'id': '2', 'project_id': '1', 'name': 'Task 2', 'description': 'Desc 2', 'status': 'Completed', 'assignee': 'Alice', 'notes': 'Test note', 'updated_date': '2026-03-02', 'created_at': '2026-03-01'}
        ])
        write_csv(users_path, ['id', 'name'], [
            {'id': '1', 'name': 'Alice'},
            {'id': '2', 'name': 'Bob'}
        ])
        
        yield projects_path, tasks_path, users_path, audit_path


class TestCSVOperations:
    def test_read_csv_empty(self, temp_csv_files):
        path = os.path.join(os.path.dirname(temp_csv_files[0]), 'empty.csv')
        assert read_csv(path) == []
    
    def test_read_csv_with_data(self, temp_csv_files):
        data = read_csv(temp_csv_files[0])
        assert len(data) == 1
        assert data[0]['name'] == 'Test Project'
    
    def test_write_csv(self, temp_csv_files):
        path = temp_csv_files[0]
        write_csv(path, ['id', 'name'], [{'id': '1', 'name': 'New'}])
        data = read_csv(path)
        assert len(data) == 1
        assert data[0]['name'] == 'New'
    
    def test_get_next_id(self, temp_csv_files):
        assert get_next_id(temp_csv_files[0]) == 2
        assert get_next_id(temp_csv_files[1]) == 3


class TestProjectProgress:
    def test_get_project_progress_with_tasks(self, temp_csv_files):
        progress = get_project_progress(1)
        assert progress == 50
    
    def test_get_project_progress_no_tasks(self, temp_csv_files):
        progress = get_project_progress(999)
        assert progress == 0
    
    def test_get_task_count(self, temp_csv_files):
        assert get_task_count(1) == 2
        assert get_task_count(999) == 0


class TestUsers:
    def test_get_users(self, temp_csv_files):
        users = get_users()
        assert len(users) == 2
        assert users[0]['name'] == 'Alice'
    
    def test_add_new_user(self, temp_csv_files):
        add_user('Charlie')
        users = get_users()
        assert len(users) == 3
        assert any(u['name'] == 'Charlie' for u in users)
    
    def test_add_duplicate_user(self, temp_csv_files):
        add_user('Alice')
        users = get_users()
        assert len(users) == 2


class TestRoutes:
    def test_index_page(self, client, temp_csv_files):
        response = client.get('/')
        assert response.status_code == 200
        assert b'Test Project' in response.data
    
    def test_project_page(self, client, temp_csv_files):
        response = client.get('/project/1')
        assert response.status_code == 200
        assert b'Task 1' in response.data
        assert b'Task 2' in response.data
    
    def test_project_page_not_found(self, client, temp_csv_files):
        response = client.get('/project/999')
        assert response.status_code == 404


class TestAddProject:
    def test_add_project(self, client, temp_csv_files):
        response = client.post('/add_project', data={
            'name': 'New Project',
            'description': 'New Description'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'New Project' in response.data
    
    def test_add_project_empty_name(self, client, temp_csv_files):
        response = client.post('/add_project', data={
            'name': '',
            'description': 'Desc'
        }, follow_redirects=True)
        
        projects = read_csv(temp_csv_files[0])
        assert len(projects) == 1


class TestAddUser:
    def test_add_user_route(self, client, temp_csv_files):
        response = client.post('/add_user', data={
            'name': 'New User',
            'project_id': '1'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        users = get_users()
        assert any(u['name'] == 'New User' for u in users)


class TestAddTask:
    def test_add_task_with_all_fields(self, client, temp_csv_files):
        response = client.post('/add_task/1', data={
            'name': 'New Task',
            'description': 'Task Description',
            'assignee': 'Alice',
            'notes': 'Test notes',
            'updated_date': '2026-03-15'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'New Task' in response.data
        
        tasks = read_csv(temp_csv_files[1])
        task = next(t for t in tasks if t['name'] == 'New Task')
        assert task['assignee'] == 'Alice'
        assert task['notes'] == 'Test notes'
        assert task['updated_date'] == '2026-03-15'
    
    def test_add_task_with_default_values(self, client, temp_csv_files):
        response = client.post('/add_task/1', data={
            'name': 'Minimal Task',
            'description': ''
        }, follow_redirects=True)
        
        tasks = read_csv(temp_csv_files[1])
        task = next(t for t in tasks if t['name'] == 'Minimal Task')
        assert task['assignee'] == ''
        assert task['notes'] == ''
        assert task['updated_date'] == datetime.now().strftime('%Y-%m-%d')
    
    def test_add_task_empty_name(self, client, temp_csv_files):
        response = client.post('/add_task/1', data={
            'name': '',
            'description': 'Desc'
        }, follow_redirects=True)
        
        tasks = read_csv(temp_csv_files[1])
        assert len(tasks) == 2


class TestUpdateTaskStatus:
    def test_update_task_with_all_fields(self, client, temp_csv_files):
        response = client.post('/update_task/1', data={
            'status': 'Completed',
            'assignee': 'Bob',
            'notes': 'Updated notes',
            'updated_date': '2026-03-20'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        tasks = read_csv(temp_csv_files[1])
        task = next(t for t in tasks if t['id'] == '1')
        assert task['status'] == 'Completed'
        assert task['assignee'] == 'Bob'
        assert task['notes'] == 'Updated notes'
        assert task['updated_date'] == '2026-03-20'
    
    def test_update_task_to_in_progress(self, client, temp_csv_files):
        response = client.post('/update_task/2', data={
            'status': 'In Progress',
            'assignee': '',
            'notes': '',
            'updated_date': ''
        }, follow_redirects=True)
        
        tasks = read_csv(temp_csv_files[1])
        task = next(t for t in tasks if t['id'] == '2')
        assert task['status'] == 'In Progress'
    
    def test_update_task_invalid(self, client, temp_csv_files):
        response = client.post('/update_task/999', data={
            'status': 'Completed',
            'assignee': '',
            'notes': '',
            'updated_date': ''
        })
        
        assert response.status_code == 404


class TestProgressCalculation:
    def test_progress_all_completed(self, client, temp_csv_files):
        client.post('/update_task/1', data={'status': 'Completed', 'assignee': '', 'notes': '', 'updated_date': ''}, follow_redirects=True)
        
        progress = get_project_progress(1)
        assert progress == 100
    
    def test_progress_none_completed(self, temp_csv_files):
        write_csv(temp_csv_files[1], ['id', 'project_id', 'name', 'description', 'status', 'assignee', 'notes', 'updated_date', 'created_at'], [
            {'id': '1', 'project_id': '1', 'name': 'Task 1', 'description': '', 'status': 'Not Started', 'assignee': '', 'notes': '', 'updated_date': '2026-03-01', 'created_at': '2026-03-01'}
        ])
        
        progress = get_project_progress(1)
        assert progress == 0
    
    def test_progress_mixed(self, temp_csv_files):
        write_csv(temp_csv_files[1], ['id', 'project_id', 'name', 'description', 'status', 'assignee', 'notes', 'updated_date', 'created_at'], [
            {'id': '1', 'project_id': '1', 'name': 'Task 1', 'description': '', 'status': 'Completed', 'assignee': '', 'notes': '', 'updated_date': '2026-03-01', 'created_at': '2026-03-01'},
            {'id': '2', 'project_id': '1', 'name': 'Task 2', 'description': '', 'status': 'In Progress', 'assignee': '', 'notes': '', 'updated_date': '2026-03-01', 'created_at': '2026-03-01'},
            {'id': '3', 'project_id': '1', 'name': 'Task 3', 'description': '', 'status': 'Not Started', 'assignee': '', 'notes': '', 'updated_date': '2026-03-01', 'created_at': '2026-03-01'},
            {'id': '4', 'project_id': '1', 'name': 'Task 4', 'description': '', 'status': 'Not Started', 'assignee': '', 'notes': '', 'updated_date': '2026-03-01', 'created_at': '2026-03-01'}
        ])
        
        progress = get_project_progress(1)
        assert progress == 25


class TestUIFeatures:
    def test_progress_bar_displayed(self, client, temp_csv_files):
        response = client.get('/')
        assert b'progress-bar' in response.data
    
    def test_status_select_displayed(self, client, temp_csv_files):
        response = client.get('/project/1')
        assert b'status' in response.data
        assert b'name="status"' in response.data
    
    def test_assignee_dropdown(self, client, temp_csv_files):
        response = client.get('/project/1')
        assert b'assignee' in response.data
        assert b'Alice' in response.data
        assert b'Bob' in response.data
    
    def test_notes_field(self, client, temp_csv_files):
        response = client.get('/project/1')
        assert b'name="notes"' in response.data
    
    def test_updated_date_field(self, client, temp_csv_files):
        response = client.get('/project/1')
        assert b'type="date"' in response.data
    
    def test_user_modal_present(self, client, temp_csv_files):
        response = client.get('/project/1')
        assert b'userModal' in response.data
    
    def test_modal_forms_present(self, client, temp_csv_files):
        response = client.get('/')
        assert b'projectModal' in response.data
        
        response = client.get('/project/1')
        assert b'taskModal' in response.data
    
    def test_changed_by_dropdown_present(self, client, temp_csv_files):
        response = client.get('/project/1')
        assert b'name="changed_by"' in response.data
    
    def test_export_button_present(self, client, temp_csv_files):
        response = client.get('/project/1')
        assert b'Export CSV' in response.data
    
    def test_audit_history_button_present(self, client, temp_csv_files):
        response = client.get('/project/1')
        assert b'History' in response.data


class TestAuditHistory:
    def test_add_audit_log(self, temp_csv_files):
        add_audit_log(1, 'Test Task', 'Status', 'Not Started', 'In Progress', 'Alice')
        audit = read_csv(temp_csv_files[3])
        assert len(audit) == 1
        assert audit[0]['task_name'] == 'Test Task'
        assert audit[0]['field_changed'] == 'Status'
        assert audit[0]['changed_by'] == 'Alice'
    
    def test_get_task_audit_history(self, temp_csv_files):
        add_audit_log(1, 'Test Task', 'Status', 'Not Started', 'In Progress', 'Alice')
        add_audit_log(1, 'Test Task', 'Assignee', '', 'Bob', 'Bob')
        
        history = get_task_audit_history(1)
        assert len(history) == 2
    
    def test_audit_history_page(self, client, temp_csv_files):
        add_audit_log(1, 'Task 1', 'Status', 'Not Started', 'Completed', 'Alice')
        
        response = client.get('/task_audit/1')
        assert response.status_code == 200
        assert b'Task 1' in response.data
        assert b'Status' in response.data
        assert b'Alice' in response.data
    
    def test_audit_history_not_found(self, client, temp_csv_files):
        response = client.get('/task_audit/999')
        assert response.status_code == 404
    
    def test_task_update_creates_audit(self, client, temp_csv_files):
        response = client.post('/update_task/1', data={
            'status': 'Completed',
            'assignee': '',
            'notes': '',
            'updated_date': '',
            'changed_by': 'Alice'
        }, follow_redirects=True)
        
        history = get_task_audit_history(1)
        assert len(history) == 1
        assert history[0]['field_changed'] == 'Status'
        assert history[0]['new_value'] == 'Completed'
    
    def test_task_create_creates_audit(self, client, temp_csv_files):
        response = client.post('/add_task/1', data={
            'name': 'New Task',
            'description': 'Desc',
            'assignee': '',
            'notes': '',
            'updated_date': '2026-03-15',
            'changed_by': 'Bob'
        }, follow_redirects=True)
        
        history = get_task_audit_history(3)
        assert len(history) == 1
        assert history[0]['field_changed'] == 'Created'


class TestExport:
    def test_export_csv(self, client, temp_csv_files):
        response = client.get('/export_project/1/csv')
        assert response.status_code == 200
        assert b'Content-Type', b'text/csv' in response.headers
        assert b'Task 1' in response.data
        assert b'Task 2' in response.data
    
    def test_export_csv_not_found(self, client, temp_csv_files):
        response = client.get('/export_project/999/csv')
        assert response.status_code == 404
    
    def test_export_contains_all_fields(self, client, temp_csv_files):
        response = client.get('/export_project/1/csv')
        data = response.data.decode('utf-8')
        assert 'ID' in data
        assert 'Name' in data
        assert 'Status' in data
        assert 'Assignee' in data
        assert 'Notes' in data
