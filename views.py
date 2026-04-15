# app/views.py - All view logic for the application

import csv
import json
import io
from datetime import datetime
from bson import ObjectId
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from .db import get_collection

# ─── Helpers ────────────────────────────────────────────────────────────────

def login_required(view_func):
    """Decorator: redirect to login if user is not in session."""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_required(view_func):
    """Decorator: redirect to dashboard if user is not admin."""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user'):
            return redirect('login')
        if request.session['user'].get('role') != 'admin':
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

def compute_stats(records):
    """Return basic stats dict from a list of electricity records."""
    usages = [r['usage'] for r in records if 'usage' in r]
    if not usages:
        return {'total': 0, 'average': 0, 'peak': 0, 'lowest': 0, 'count': 0}
    return {
        'total':   round(sum(usages), 2),
        'average': round(sum(usages) / len(usages), 2),
        'peak':    round(max(usages), 2),
        'lowest':  round(min(usages), 2),
        'count':   len(usages),
    }

def detect_anomalies(records):
    """Flag records whose usage is above PEAK_THRESHOLD or below LOW_THRESHOLD."""
    high = settings.PEAK_THRESHOLD
    low  = settings.LOW_THRESHOLD
    anomalies = []
    for r in records:
        usage = r.get('usage', 0)
        if usage > high:
            anomalies.append({'record': r, 'type': 'HIGH', 'threshold': high})
        elif usage < low:
            anomalies.append({'record': r, 'type': 'LOW',  'threshold': low})
    return anomalies

# ─── Auth Views ──────────────────────────────────────────────────────────────

def login_view(request):
    """Handle login form submission and session creation."""
    if request.session.get('user'):
        return redirect('dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        users = get_collection('users')
        user = users.find_one({'username': username})
        if user and check_password(password, user['password']):
            # Store safe user info in session (no password)
            request.session['user'] = {'username': user['username'], 'role': user['role']}
            return redirect('dashboard')
        error = 'Invalid username or password.'
    return render(request, 'login.html', {'error': error})


def signup_view(request):
    """Handle new user registration."""
    if request.session.get('user'):
        return redirect('dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        role     = request.POST.get('role', 'user')
        users    = get_collection('users')

        if users.find_one({'username': username}):
            error = 'Username already exists.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        else:
            users.insert_one({
                'username': username,
                'password': make_password(password),
                'role':     role,
                'created':  datetime.utcnow(),
            })
            return redirect('login')
    return render(request, 'signup.html', {'error': error})


def logout_view(request):
    """Clear session and redirect to login."""
    request.session.flush()
    return redirect('login')

# ─── Dashboard ───────────────────────────────────────────────────────────────

def parse_date(date_str):
    """Parse date string in either DD-MM-YYYY or YYYY-MM-DD format, return YYYY-MM-DD."""
    date_str = date_str.strip()
    for fmt in ('%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return date_str  # return as-is if unparseable


@login_required
def dashboard(request):
    """Main dashboard: stats + chart data + optional filters."""
    col = get_collection('electricity_data')

    region_filter = request.GET.get('region', '').strip()
    date_from     = request.GET.get('date_from', '').strip()
    date_to       = request.GET.get('date_to', '').strip()

    # Always fetch all regions for the dropdown (unfiltered)
    all_regions = sorted(col.distinct('region'))

    # Fetch all records and normalise date to YYYY-MM-DD for consistent comparison
    all_records = list(col.find({}, {'_id': 0}))
    for r in all_records:
        r['date'] = parse_date(r.get('date', ''))

    records = []
    for r in all_records:
        # Region filter
        if region_filter and r.get('region', '') != region_filter:
            continue
        # Date range filter (safe string compare since both are YYYY-MM-DD now)
        if date_from and r.get('date', '') < date_from:
            continue
        if date_to and r.get('date', '') > date_to:
            continue
        records.append(r)

    stats     = compute_stats(records)
    anomalies = detect_anomalies(records)

    # Line chart: sort by date
    sorted_records = sorted(records, key=lambda r: r.get('date', ''))
    line_labels = [r['date'] for r in sorted_records]
    line_data   = [r['usage'] for r in sorted_records]

    # Bar / Pie chart: per region
    region_map = {}
    for r in records:
        region_map.setdefault(r.get('region', 'Unknown'), []).append(r.get('usage', 0))
    bar_labels = list(region_map.keys())
    bar_data   = [round(sum(v) / len(v), 2) for v in region_map.values()]
    pie_data   = [round(sum(v), 2) for v in region_map.values()]

    context = {
        'stats':          stats,
        'records':        sorted_records[:50],
        'anomalies':      anomalies,
        'all_regions':    all_regions,
        'region_filter':  region_filter,
        'date_from':      date_from,
        'date_to':        date_to,
        'line_labels':    json.dumps(line_labels),
        'line_data':      json.dumps(line_data),
        'bar_labels':     json.dumps(bar_labels),
        'bar_data':       json.dumps(bar_data),
        'pie_labels':     json.dumps(bar_labels),
        'pie_data':       json.dumps(pie_data),
        'peak_threshold': settings.PEAK_THRESHOLD,
    }
    return render(request, 'dashboard.html', context)

# ─── Analytics ───────────────────────────────────────────────────────────────

@login_required
def analytics(request):
    """Deep analytics: trends, peak periods, high-consumption regions."""
    col     = get_collection('electricity_data')
    records = list(col.find({}, {'_id': 0}))
    # Normalise dates to YYYY-MM-DD
    for r in records:
        r['date'] = parse_date(r.get('date', ''))
    stats   = compute_stats(records)

    # Peak demand periods (top 5 by usage)
    peak_periods = sorted(records, key=lambda r: r.get('usage', 0), reverse=True)[:5]

    # High consumption regions (above average)
    region_totals = {}
    for r in records:
        reg = r.get('region', 'Unknown')
        region_totals.setdefault(reg, 0)
        region_totals[reg] += r.get('usage', 0)
    avg_region = sum(region_totals.values()) / len(region_totals) if region_totals else 0
    high_regions = {k: round(v, 2) for k, v in region_totals.items() if v > avg_region}

    # Trend: monthly average
    monthly = {}
    for r in records:
        month = r.get('date', '')[:7]   # YYYY-MM
        monthly.setdefault(month, []).append(r.get('usage', 0))
    trend_labels = sorted(monthly.keys())
    trend_data   = [round(sum(monthly[m])/len(monthly[m]), 2) for m in trend_labels]

    anomalies = detect_anomalies(records)

    stats_list = [
        ('Total Consumption (kWh)', stats['total'],   'primary'),
        ('Average Usage (kWh)',     stats['average'], 'success'),
        ('Peak Usage (kWh)',        stats['peak'],    'danger'),
        ('Lowest Usage (kWh)',      stats['lowest'],  'warning'),
    ]
    context = {
        'stats':        stats,
        'stats_list':   stats_list,
        'peak_periods': peak_periods,
        'high_regions': high_regions,
        'anomalies':    anomalies,
        'trend_labels': json.dumps(trend_labels),
        'trend_data':   json.dumps(trend_data),
    }
    return render(request, 'analytics.html', context)

# ─── Admin Panel ─────────────────────────────────────────────────────────────

@admin_required
def admin_panel(request):
    """Admin view: list all records with add/edit/delete options."""
    col     = get_collection('electricity_data')
    records = list(col.find())
    # Convert ObjectId to string and expose as 'id' for template use
    for r in records:
        r['id'] = str(r['_id'])
        del r['_id']
    regions = get_collection('regions').distinct('name')
    stats   = compute_stats(records)
    return render(request, 'admin_panel.html', {'records': records, 'regions': regions, 'stats': stats})


@admin_required
def add_data(request):
    """Add a single electricity record."""
    if request.method == 'POST':
        region = request.POST.get('region', '').strip()
        date   = request.POST.get('date', '').strip()
        usage  = request.POST.get('usage', '0').strip()
        try:
            get_collection('electricity_data').insert_one({
                'region': region,
                'date':   date,
                'usage':  float(usage),
            })
            # Auto-add region if new
            get_collection('regions').update_one(
                {'name': region}, {'$setOnInsert': {'name': region}}, upsert=True
            )
        except ValueError:
            pass
    return redirect('admin_panel')


@admin_required
def edit_data(request, record_id):
    """Update an existing electricity record."""
    col = get_collection('electricity_data')
    if request.method == 'POST':
        region = request.POST.get('region', '').strip()
        date   = request.POST.get('date', '').strip()
        usage  = request.POST.get('usage', '0').strip()
        try:
            col.update_one(
                {'_id': ObjectId(record_id)},
                {'$set': {'region': region, 'date': date, 'usage': float(usage)}}
            )
        except Exception:
            pass
        return redirect('admin_panel')

    record = col.find_one({'_id': ObjectId(record_id)})
    if record:
        record['id'] = str(record['_id'])
        del record['_id']
    return render(request, 'admin_panel.html', {'edit_record': record, 'records': [], 'regions': [], 'stats': compute_stats([])})


@admin_required
def delete_data(request, record_id):
    """Delete an electricity record by ID."""
    get_collection('electricity_data').delete_one({'_id': ObjectId(record_id)})
    return redirect('admin_panel')


@admin_required
def upload_csv(request):
    """Parse uploaded CSV and bulk-insert into MongoDB."""
    error   = None
    success = None
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        try:
            # Decode with utf-8-sig to strip BOM if present
            raw = csv_file.read()
            decoded = raw.decode('utf-8-sig').strip()

            reader  = csv.DictReader(io.StringIO(decoded))

            # Normalize header names: strip spaces and lowercase
            reader.fieldnames = [f.strip().lower() for f in reader.fieldnames]

            records = []
            regions = set()
            skipped = 0
            for row in reader:
                # Normalize each key in the row
                row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                region = row.get('region', '')
                date   = row.get('date', '')
                usage  = row.get('usage', '')
                if region and date and usage:
                    try:
                        records.append({
                            'region': region,
                            'date':   date,
                            'usage':  float(usage),
                        })
                        regions.add(region)
                    except ValueError:
                        skipped += 1
                else:
                    skipped += 1

            if records:
                get_collection('electricity_data').insert_many(records)
                for reg in regions:
                    get_collection('regions').update_one(
                        {'name': reg}, {'$setOnInsert': {'name': reg}}, upsert=True
                    )
                msg = f'{len(records)} records uploaded successfully.'
                if skipped:
                    msg += f' ({skipped} rows skipped due to missing/invalid data)'
                success = msg
            else:
                # Show detected headers to help user debug
                error = (f'No valid rows found. Detected columns: '
                         f'{list(reader.fieldnames)}. '
                         f'Expected: region, date, usage')
        except Exception as e:
            error = f'Error processing file: {e}'
    return render(request, 'upload.html', {'error': error, 'success': success})

# ─── Export ──────────────────────────────────────────────────────────────────

@login_required
def export_csv(request):
    """Export all electricity data as a downloadable CSV file."""
    records  = list(get_collection('electricity_data').find({}, {'_id': 0}))
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="electricity_data.csv"'
    writer = csv.writer(response)
    writer.writerow(['region', 'date', 'usage'])
    for r in records:
        writer.writerow([r.get('region'), r.get('date'), r.get('usage')])
    return response
