# Project Task Tracker - Specification

## 1. Project Overview
- **Project Name**: Project Task Tracker
- **Type**: Simple web application
- **Core Functionality**: Track and manage task statuses within projects using local CSV files
- **Target Users**: Individuals or small teams managing project tasks

## 2. UI/UX Specification

### Layout Structure
- **Header**: App title, navigation
- **Main Content**: Project list or task list depending on view
- **Footer**: Simple copyright

### Visual Design
- **Color Palette**:
  - Background: `#1a1a2e` (dark navy)
  - Card Background: `#16213e` (darker blue)
  - Card Alternate: `#1a2844` (lighter blue for alternating rows)
  - Primary: `#0f3460` (deep blue)
  - Primary Border: `#1a4a7a` (lighter blue for inputs)
  - Accent: `#e94560` (coral red)
  - Text Primary: `#eaeaea`
  - Text Secondary: `#a0a0a0`
  - Status Colors:
    - Not Started: `#3d3d3d`
    - In Progress: `#3d3d2a`
    - Completed: `#1d3d2a`
- **Typography**:
  - Font: 'Segoe UI', system-ui, sans-serif
  - Headings: 1.5rem - 2rem, bold
  - Body: 1rem
- **Spacing**: 8px base unit, 16px, 24px, 32px increments

### Components
- **Project Card**: Shows project name, description, task count, progress bar
- **Task Card**: Each task displayed as a horizontal card in a single line
- **Task Fields**: Status, Assignee, Updated Date, Notes, Changed By, History, Update
- **Status Select**: Dropdown for changing task status
- **Assignee Dropdown**: Select from users list (default empty)
- **Notes Field**: Reduced width textarea for task notes
- **Changed By Dropdown**: Required dropdown to track who made changes
- **History Button**: Link to view audit history for each task
- **Export Button**: Export project tasks to CSV
- **Progress Bar**: Visual completion percentage
- **Buttons**: Add project, add task, add user, export, update status, view history

### Views
1. **Projects View**: List of all projects with summary and progress bars
2. **Tasks View**: Tasks displayed as horizontal cards with all fields inline
3. **Audit History View**: Detailed change history for each task

## 3. Functionality Specification

### Core Features
1. **View Projects**: Display all projects from projects.csv with progress
2. **View Tasks**: Display tasks for selected project as card layout
3. **Update Task Status**: Change task status via dropdown (Not Started, In Progress, Completed)
4. **Add Project**: Form to create new project (saves to CSV)
5. **Add Task**: Form to create new task with assignee, notes, updated date
6. **Progress Calculation**: Auto-calculate project completion based on tasks
7. **User Management**: Add users to the system (stored in users.csv)
8. **Assignee Tracking**: Assign tasks to users from dropdown
9. **Task Notes**: Add/edit notes/comments for each task
10. **Updated Date**: Track when task was last updated with date picker
11. **Audit History**: Track all changes to tasks (who changed what and when)
12. **Changed By Required**: Must select who is making changes
13. **Export to CSV**: Download project tasks as CSV file

### Data Handling
- **projects.csv**: id, name, description, created_at
- **tasks.csv**: id, project_id, name, description, status, assignee, notes, updated_date, created_at
- **users.csv**: id, name
- **audit.csv**: id, task_id, task_name, field_changed, old_value, new_value, changed_by, changed_at
- CSV files stored in same directory as application

### Status Options
- Not Started
- In Progress
- Completed

## 4. Acceptance Criteria
- [x] Projects list displays on home page
- [x] Clicking a project shows its tasks
- [x] Task status can be changed via dropdown
- [x] Changes persist to CSV files
- [x] Progress bar reflects task completion
- [x] New projects can be added
- [x] New tasks can be added
- [x] Responsive design works on mobile/desktop
- [x] Assignee dropdown with default empty value
- [x] New users can be added and appear in assignee dropdown
- [x] Notes/comments field for each task
- [x] Updated date with date picker
- [x] Audit history tracks changes (who, what, when)
- [x] Changed By field is required for any updates
- [x] Export project to CSV functionality
- [x] Task cards display in single line with alternating row colors
- [x] Notes field has reduced width in UI
