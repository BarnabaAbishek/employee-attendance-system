from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from firebase_config import db, auth
from firebase_admin import firestore
from datetime import datetime, timedelta
import pandas as pd
from fpdf import FPDF
import io
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')

# ============ HELPER FUNCTIONS ============
def is_logged_in():
    """Check if user is logged in"""
    return 'user' in session

def get_user_id():
    """Get current user's Firebase UID"""
    return session.get('user', {}).get('uid')

def require_login(func):
    """Decorator to require login"""
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            flash('Please login first!', 'danger')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

def safe_get(dictionary, key, default=None):
    """Safely get value from dictionary"""
    return dictionary.get(key, default)

# ============ AUTHENTICATION ROUTES ============
@app.route('/')
def index():
    """Home page"""
    if is_logged_in():
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # DEMO LOGIN - For testing without Firebase Auth
        if email == 'admin@company.com' and password == 'admin123':
            session['user'] = {
                'uid': 'demo-admin-001',
                'email': email,
                'name': 'Admin User'
            }
            flash('Login successful! (Demo Mode)', 'success')
            return redirect(url_for('dashboard'))
        elif email == 'manager@company.com' and password == 'manager123':
            session['user'] = {
                'uid': 'demo-manager-001',
                'email': email,
                'name': 'Manager User'
            }
            flash('Login successful! (Demo Mode)', 'success')
            return redirect(url_for('dashboard'))
        else:
            try:
                # Firebase Authentication (for real users)
                user = auth.get_user_by_email(email)
                session['user'] = {
                    'uid': user.uid,
                    'email': user.email,
                    'name': user.display_name or email.split('@')[0]
                }
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                flash(f'Login failed: {str(e)}', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    """Register new user"""
    email = request.form.get('email')
    password = request.form.get('password')
    name = request.form.get('name')
    
    try:
        # Create user in Firebase Authentication
        user = auth.create_user(
            email=email,
            password=password,
            display_name=name
        )
        
        # Store additional user data in Firestore
        user_data = {
            'email': email,
            'name': name,
            'created_at': datetime.now(),
            'role': 'admin'  # Default role
        }
        db.collection('users').document(user.uid).set(user_data)
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    except Exception as e:
        flash(f'Registration failed: {str(e)}', 'danger')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Logout user"""
    session.pop('user', None)
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))

# ============ DASHBOARD ============
@app.route('/dashboard')
@require_login
def dashboard():
    """Main dashboard"""
    # Get statistics
    employees_ref = db.collection('employees')
    employees_count = len(list(employees_ref.stream()))
    
    # Get today's attendance
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get all attendance and filter locally
    all_attendance = list(db.collection('attendance').stream())
    today_attendance = 0
    recent_list = []
    
    for record in all_attendance:
        data = record.to_dict()
        data['id'] = record.id
        
        # Count today's attendance
        if data.get('date') == today:
            today_attendance += 1
        
        # Add to recent list for sorting
        recent_list.append(data)
    
    # Sort by timestamp and get recent 10
    recent_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    recent_list = recent_list[:10]
    
    return render_template('index.html', 
                         employees_count=employees_count,
                         today_attendance=today_attendance,
                         recent_activity=recent_list,
                         user=session['user'])

# ============ EMPLOYEE MANAGEMENT ============
@app.route('/employees')
@require_login
def view_employees():
    """View all employees - FIXED VERSION"""
    employees_ref = db.collection('employees').stream()
    employees = []
    
    for emp in employees_ref:
        data = emp.to_dict()
        data['id'] = emp.id
        
        # Ensure all fields have default values
        data['name'] = safe_get(data, 'name', 'Unknown')
        data['employee_id'] = safe_get(data, 'employee_id', f"EMP{emp.id[:6]}")
        data['department'] = safe_get(data, 'department', 'Not Assigned')
        data['position'] = safe_get(data, 'position', 'Employee')
        data['email'] = safe_get(data, 'email', '')
        data['phone'] = safe_get(data, 'phone', '')
        data['status'] = safe_get(data, 'status', 'active')
        data['join_date'] = safe_get(data, 'join_date', '')
        
        employees.append(data)
    
    return render_template('add_employee.html', employees=employees)

@app.route('/add_employee', methods=['POST'])
@require_login
def add_employee():
    """Add new employee"""
    try:
        employee_data = {
            'name': request.form.get('name', '').strip(),
            'employee_id': request.form.get('employee_id', '').strip(),
            'department': request.form.get('department', '').strip(),
            'position': request.form.get('position', '').strip(),
            'email': request.form.get('email', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'join_date': request.form.get('join_date', ''),
            'status': request.form.get('status', 'active').strip(),
            'created_at': datetime.now(),
            'created_by': get_user_id()
        }
        
        # Validate required fields
        if not employee_data['name'] or not employee_data['employee_id']:
            flash('Name and Employee ID are required!', 'danger')
            return redirect(url_for('view_employees'))
        
        # Add to Firestore
        doc_ref = db.collection('employees').add(employee_data)
        
        flash(f'Employee {employee_data["name"]} added successfully!', 'success')
        return redirect(url_for('view_employees'))
    except Exception as e:
        flash(f'Error adding employee: {str(e)}', 'danger')
        return redirect(url_for('view_employees'))

@app.route('/delete_employee/<employee_id>')
@require_login
def delete_employee(employee_id):
    """Delete employee"""
    try:
        db.collection('employees').document(employee_id).delete()
        flash('Employee deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting employee: {str(e)}', 'danger')
    
    return redirect(url_for('view_employees'))

# ============ EMPLOYEE EDIT FUNCTIONALITY ============
@app.route('/get_employee/<employee_id>')
@require_login
def get_employee(employee_id):
    """Get employee details for editing - FIXED VERSION"""
    try:
        emp_ref = db.collection('employees').document(employee_id)
        emp_doc = emp_ref.get()
        
        if emp_doc.exists:
            employee_data = emp_doc.to_dict()
            employee_data['id'] = employee_id
            
            # Ensure all fields exist with default values
            employee_data['name'] = safe_get(employee_data, 'name', '')
            employee_data['employee_id'] = safe_get(employee_data, 'employee_id', '')
            employee_data['department'] = safe_get(employee_data, 'department', '')
            employee_data['position'] = safe_get(employee_data, 'position', '')
            employee_data['email'] = safe_get(employee_data, 'email', '')
            employee_data['phone'] = safe_get(employee_data, 'phone', '')
            employee_data['join_date'] = safe_get(employee_data, 'join_date', '')
            employee_data['status'] = safe_get(employee_data, 'status', 'active')
            
            # Handle Firestore timestamp conversion
            if 'created_at' in employee_data:
                if hasattr(employee_data['created_at'], 'timestamp'):
                    # Convert Firestore timestamp to Python datetime
                    employee_data['created_at'] = employee_data['created_at'].strftime('%Y-%m-%d')
                elif isinstance(employee_data['created_at'], datetime):
                    employee_data['created_at'] = employee_data['created_at'].strftime('%Y-%m-%d')
            
            return jsonify({
                'success': True,
                'employee': employee_data
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Employee not found'
            })
    except Exception as e:
        print(f"Error in get_employee: {str(e)}")  # Debug log
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/update_employee', methods=['POST'])
@require_login
def update_employee():
    """Update employee details"""
    try:
        employee_id = request.form.get('employee_id')
        
        updated_data = {
            'name': request.form.get('name', '').strip(),
            'employee_id': request.form.get('employee_code', '').strip(),
            'department': request.form.get('department', '').strip(),
            'position': request.form.get('position', '').strip(),
            'email': request.form.get('email', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'join_date': request.form.get('join_date', ''),
            'status': request.form.get('status', 'active').strip(),
            'updated_at': datetime.now(),
            'updated_by': get_user_id()
        }
        
        # Validate required fields
        if not updated_data['name'] or not updated_data['employee_id']:
            flash('Name and Employee ID are required!', 'danger')
            return redirect(url_for('view_employees'))
        
        # Remove empty strings
        updated_data = {k: v for k, v in updated_data.items() if v is not None and v != ''}
        
        # Update in Firestore
        db.collection('employees').document(employee_id).update(updated_data)
        
        flash(f'Employee {updated_data["name"]} updated successfully!', 'success')
        return redirect(url_for('view_employees'))
    except Exception as e:
        flash(f'Error updating employee: {str(e)}', 'danger')
        return redirect(url_for('view_employees'))

# ============ ATTENDANCE MANAGEMENT ============
@app.route('/attendance')
@require_login
def attendance_page():
    """Attendance marking page"""
    # Get active employees
    all_employees = list(db.collection('employees').stream())
    employees = []
    
    for emp in all_employees:
        data = emp.to_dict()
        data['id'] = emp.id
        
        # Use safe_get for status
        status = safe_get(data, 'status', 'active')
        if status == 'active':
            employees.append(data)
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('attendance.html', 
                         employees=employees, 
                         today=today,
                         user=session['user'])

@app.route('/mark_attendance', methods=['POST'])
@require_login
def mark_attendance():
    """Mark attendance for employees"""
    try:
        employee_id = request.form.get('employee_id')
        status = request.form.get('status')  # present, absent, late, half-day
        date = request.form.get('date')
        notes = request.form.get('notes', '')
        
        if not employee_id or not status:
            return jsonify({
                'success': False,
                'message': 'Employee ID and status are required!'
            })
        
        # Check if attendance already marked for today
        all_attendance = list(db.collection('attendance').stream())
        already_marked = False
        
        for record in all_attendance:
            data = record.to_dict()
            if data.get('employee_id') == employee_id and data.get('date') == date:
                already_marked = True
                break
        
        if already_marked:
            return jsonify({
                'success': False,
                'message': 'Attendance already marked for today!'
            })
        
        # Get employee details
        emp_doc = db.collection('employees').document(employee_id).get()
        if not emp_doc.exists:
            return jsonify({
                'success': False,
                'message': 'Employee not found!'
            })
        
        employee_data = emp_doc.to_dict()
        
        # Create attendance record
        attendance_data = {
            'employee_id': employee_id,
            'employee_name': safe_get(employee_data, 'name', 'Unknown'),
            'employee_department': safe_get(employee_data, 'department', ''),
            'date': date,
            'status': status,
            'notes': notes,
            'marked_by': get_user_id(),
            'marked_by_name': session['user']['name'],
            'timestamp': datetime.now()
        }
        
        # Add to Firestore
        db.collection('attendance').add(attendance_data)
        
        return jsonify({
            'success': True,
            'message': f'Attendance marked for {employee_data.get("name", "Employee")}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

# ============ VIEW ATTENDANCE WITH FILTERING ============
@app.route('/view_attendance')
@require_login
def view_attendance():
    """View attendance records - WITH WORKING FILTERS"""
    # Get filter parameters
    date_filter = request.args.get('date', '')
    employee_filter = request.args.get('employee', '')
    department_filter = request.args.get('department', '')
    status_filter = request.args.get('status', '')
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get ALL attendance records (simple query)
    all_records = []
    attendance_ref = db.collection('attendance').stream()
    
    for record in attendance_ref:
        data = record.to_dict()
        data['id'] = record.id
        
        # Use safe_get for all fields
        data['employee_name'] = safe_get(data, 'employee_name', 'Unknown')
        data['employee_department'] = safe_get(data, 'employee_department', '')
        data['date'] = safe_get(data, 'date', '')
        data['status'] = safe_get(data, 'status', '')
        data['marked_by_name'] = safe_get(data, 'marked_by_name', 'Admin')
        data['notes'] = safe_get(data, 'notes', '')
        
        # Convert timestamp to string for display
        if 'timestamp' in data:
            timestamp_obj = data['timestamp']
            try:
                # Handle Firestore timestamp
                if hasattr(timestamp_obj, 'strftime'):
                    data['timestamp_str'] = timestamp_obj.strftime('%I:%M %p')
                # Handle datetime object
                elif isinstance(timestamp_obj, datetime):
                    data['timestamp_str'] = timestamp_obj.strftime('%I:%M %p')
                # Handle string timestamp
                elif isinstance(timestamp_obj, str):
                    # Try to parse string to datetime
                    try:
                        dt = datetime.fromisoformat(timestamp_obj.replace('Z', '+00:00'))
                        data['timestamp_str'] = dt.strftime('%I:%M %p')
                    except:
                        data['timestamp_str'] = timestamp_obj
                else:
                    data['timestamp_str'] = str(timestamp_obj)
            except:
                data['timestamp_str'] = ''
        else:
            data['timestamp_str'] = ''
        
        all_records.append(data)
    
    # Apply filters in Python (no Firebase query errors)
    filtered_records = all_records
    
    if date_filter:
        filtered_records = [r for r in filtered_records if r.get('date') == date_filter]
    
    if employee_filter:
        filtered_records = [r for r in filtered_records if r.get('employee_id') == employee_filter]
    
    if department_filter:
        filtered_records = [r for r in filtered_records if r.get('employee_department') == department_filter]
    
    if status_filter:
        filtered_records = [r for r in filtered_records if r.get('status') == status_filter]
    
    # Sort by timestamp (newest first)
    def get_sort_key(record):
        timestamp = record.get('timestamp')
        if timestamp:
            # Try to convert to datetime for sorting
            try:
                if hasattr(timestamp, 'timestamp'):
                    return timestamp.timestamp()
                elif isinstance(timestamp, datetime):
                    return timestamp.timestamp()
                elif isinstance(timestamp, str):
                    # Try to parse string
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        return dt.timestamp()
                    except:
                        return 0
            except:
                return 0
        return 0
    
    filtered_records.sort(key=get_sort_key, reverse=True)
    
    # Get employees for filter dropdown
    employees_ref = db.collection('employees').stream()
    employees = []
    for emp in employees_ref:
        data = emp.to_dict()
        data['id'] = emp.id
        
        # Use safe_get for employee data
        data['name'] = safe_get(data, 'name', 'Unknown')
        data['employee_id'] = safe_get(data, 'employee_id', f"EMP{emp.id[:6]}")
        data['department'] = safe_get(data, 'department', 'Not Assigned')
        
        employees.append(data)
    
    # Get unique departments
    departments = []
    for emp in employees:
        dept = emp.get('department')
        if dept and dept not in departments:
            departments.append(dept)
    
    # Calculate statistics
    present_count = sum(1 for r in filtered_records if r.get('status') == 'present')
    absent_count = sum(1 for r in filtered_records if r.get('status') == 'absent')
    other_count = len(filtered_records) - present_count - absent_count
    
    return render_template('view_attendance.html',
                         records=filtered_records,
                         employees=employees,
                         departments=departments,
                         date_today=today,
                         stats={
                             'present': present_count,
                             'absent': absent_count,
                             'other': other_count,
                             'total': len(filtered_records)
                         },
                         filters={
                             'date': date_filter,
                             'employee': employee_filter,
                             'department': department_filter,
                             'status': status_filter
                         })

# ============ REPORTS - SIMPLIFIED VERSION ============
@app.route('/generate_report')
@require_login
def generate_report():
    """Generate attendance report - NO FIREBASE INDEX ERRORS"""
    try:
        report_type = request.args.get('type', 'excel')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        department = request.args.get('department', '')
        
        if not start_date or not end_date:
            flash('Please select start and end dates!', 'danger')
            return redirect(url_for('view_attendance'))
        
        # Get ALL attendance records (simple query - no filters)
        all_records = []
        attendance_ref = db.collection('attendance').stream()
        
        for record in attendance_ref:
            data = record.to_dict()
            all_records.append(data)
        
        if not all_records:
            flash('No attendance records found!', 'warning')
            return redirect(url_for('view_attendance'))
        
        # Convert to DataFrame
        df = pd.DataFrame(all_records)
        
        # Filter by date in Python (not in query)
        if start_date and end_date:
            mask = (df['date'] >= start_date) & (df['date'] <= end_date)
            df = df.loc[mask]
        
        if department:
            mask = df['employee_department'] == department
            df = df.loc[mask]
        
        if df.empty:
            flash('No records found for the selected criteria!', 'warning')
            return redirect(url_for('view_attendance'))
        
        # Generate report based on type
        if report_type == 'excel':
            return generate_excel_report(df, start_date, end_date)
        elif report_type == 'pdf':
            return generate_pdf_report(df, start_date, end_date)
        else:
            # Return JSON for chart
            summary = df.groupby('status').size().to_dict()
            return jsonify({
                'success': True,
                'summary': summary,
                'total': len(df)
            })
            
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'danger')
        return redirect(url_for('view_attendance'))

def generate_excel_report(df, start_date, end_date):
    """Generate Excel report"""
    # Create Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Attendance', index=False)
    
    output.seek(0)
    
    # Create filename
    filename = f'attendance_report_{start_date}_to_{end_date}.xlsx'
    
    return send_file(output,
                    download_name=filename,
                    as_attachment=True,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

def generate_pdf_report(df, start_date, end_date):
    """Generate PDF report"""
    pdf = FPDF()
    pdf.add_page()
    
    # Add title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(200, 10, 'Attendance Report', 0, 1, 'C')
    
    # Add period
    pdf.set_font('Arial', '', 12)
    pdf.cell(200, 10, f'Period: {start_date} to {end_date}', 0, 1, 'C')
    pdf.ln(10)
    
    # Add table headers
    pdf.set_font('Arial', 'B', 12)
    col_widths = [40, 40, 30, 30, 40]
    headers = ['Employee', 'Department', 'Date', 'Status', 'Marked By']
    
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1)
    pdf.ln()
    
    # Add table rows
    pdf.set_font('Arial', '', 10)
    for _, row in df.iterrows():
        pdf.cell(col_widths[0], 10, str(row.get('employee_name', '')), 1)
        pdf.cell(col_widths[1], 10, str(row.get('employee_department', '')), 1)
        pdf.cell(col_widths[2], 10, str(row.get('date', '')), 1)
        pdf.cell(col_widths[3], 10, str(row.get('status', '')), 1)
        pdf.cell(col_widths[4], 10, str(row.get('marked_by_name', '')), 1)
        pdf.ln()
    
    # Save to bytes
    output = io.BytesIO()
    pdf_bytes = pdf.output()
    output.write(pdf_bytes)
    output.seek(0)
    
    # Create filename
    filename = f'attendance_report_{start_date}_to_{end_date}.pdf'
    
    return send_file(output,
                    download_name=filename,
                    as_attachment=True,
                    mimetype='application/pdf')

# ============ API ENDPOINTS ============
@app.route('/api/attendance_stats')
@require_login
def attendance_stats():
    """Get attendance statistics for dashboard"""
    # Get all attendance records
    all_records = list(db.collection('attendance').stream())
    
    # Get date range (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Process data
    daily_counts = {}
    status_counts = {'present': 0, 'absent': 0, 'late': 0, 'half-day': 0}
    
    for record in all_records:
        data = record.to_dict()
        date = data.get('date', '')
        status = data.get('status', '')
        
        # Filter by date range
        if date and start_date.strftime('%Y-%m-%d') <= date <= end_date.strftime('%Y-%m-%d'):
            # Count by date
            daily_counts[date] = daily_counts.get(date, 0) + 1
            
            # Count by status
            if status in status_counts:
                status_counts[status] += 1
    
    # Prepare response
    dates = sorted(daily_counts.keys())
    counts = [daily_counts.get(date, 0) for date in dates]
    
    # Get total employees
    total_employees = len(list(db.collection('employees').stream()))
    
    return jsonify({
        'dates': dates,
        'counts': counts,
        'status_counts': status_counts,
        'total_employees': total_employees
    })

# ============ ERROR HANDLERS ============
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

# ============ RUN APPLICATION ============
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)