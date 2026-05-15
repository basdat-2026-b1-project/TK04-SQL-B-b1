from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.contrib.auth.hashers import make_password
from datetime import date
from django.core.paginator import Paginator
from django.db import transaction
from member.views import login_required_member

DUMMY_MEMBERS = [
    {'nomor': 'M0001', 'nama': 'Mr. John William Doe', 'email': 'john@example.com',
     'tier': 'Gold', 'total_miles': 45000, 'award_miles': 32000, 'bergabung': '2024-01-15'},
    {'nomor': 'M0002', 'nama': 'Mrs. Jane Smith', 'email': 'jane@example.com',
     'tier': 'Silver', 'total_miles': 20000, 'award_miles': 15000, 'bergabung': '2024-03-10'},
    {'nomor': 'M0003', 'nama': 'Mr. Budi Anto Santoso', 'email': 'budi@example.com',
     'tier': 'Blue', 'total_miles': 5000, 'award_miles': 3500, 'bergabung': '2024-08-20'},
    {'nomor': 'M0004', 'nama': 'Mr. John Lennon', 'email': 'johnlennon@gmail.com',
     'tier': 'Blue', 'total_miles': 0, 'award_miles': 0, 'bergabung': '2026-04-12'},
    {'nomor': 'M0005', 'nama': 'Ms. Sari Dewi', 'email': 'sari@example.com',
     'tier': 'Platinum', 'total_miles': 120000, 'award_miles': 95000, 'bergabung': '2022-05-01'},
]


DUMMY_HADIAH_STAF = [
    {'kode': 'RWD-001', 'nama': 'Tiket Domestik PP', 'deskripsi': 'Tiket pulang-pergi domestik',
     'penyedia': 'Garuda Indonesia', 'tipe_penyedia': 'airline',
     'miles': 15000, 'periode': '2024-01-01 — 2025-12-31', 'aktif': True},
    {'kode': 'RWD-002', 'nama': 'Upgrade Business Class', 'deskripsi': 'Upgrade economy ke business',
     'penyedia': 'Garuda Indonesia', 'tipe_penyedia': 'airline',
     'miles': 25000, 'periode': '2024-01-01 — 2025-12-31', 'aktif': True},
    {'kode': 'RWD-003', 'nama': 'Voucher Hotel Rp 500.000', 'deskripsi': 'Voucher hotel Indonesia',
     'penyedia': 'TravelokaPartner', 'tipe_penyedia': 'partner',
     'miles': 8000, 'periode': '2024-06-01 — 2025-06-30', 'aktif': True},
    {'kode': 'RWD-004', 'nama': 'Akses Lounge 1x', 'deskripsi': 'Akses lounge premium 1x',
     'penyedia': 'Plaza Premium', 'tipe_penyedia': 'partner',
     'miles': 3000, 'periode': '2024-01-01 — 2025-12-31', 'aktif': False},
]

DUMMY_MITRA = [
    {'email': 'partner@traveloka.com', 'id_penyedia': 3, 'nama': 'TravelokaPartner', 'tanggal': '2023-01-15'},
    {'email': 'partner@plazapremium.com', 'id_penyedia': 4, 'nama': 'Plaza Premium', 'tanggal': '2023-06-01'},
    {'email': 'partner@hotelindo.com', 'id_penyedia': 5, 'nama': 'HotelIndo', 'tanggal': '2024-01-10'},
    {'email': 'partner@rentalcar.com', 'id_penyedia': 6, 'nama': 'RentalCar Express', 'tanggal': '2024-03-20'},
]

PENYEDIA_CHOICES = [
    ('1', 'GA - Garuda Indonesia (airline)'),
    ('2', 'SQ - Singapore Airlines (airline)'),
    ('3', 'TravelokaPartner (mitra)'),
    ('4', 'Plaza Premium (mitra)'),
    ('5', 'HotelIndo (mitra)'),
]

DUMMY_TRANSAKSI_LAPORAN = [
    {'tipe': 'Transfer', 'member': 'John W. Doe', 'email': 'john@example.com',
     'jumlah': -5000, 'timestamp': '2025-01-15 10:30'},
    {'tipe': 'Redeem', 'member': 'John W. Doe', 'email': 'john@example.com',
     'jumlah': -3000, 'timestamp': '2025-01-20 16:00'},
    {'tipe': 'Package', 'member': 'Jane Smith', 'email': 'jane@example.com',
     'jumlah': 5000, 'timestamp': '2025-02-01 09:15'},
    {'tipe': 'Klaim', 'member': 'Budi A. Santoso', 'email': 'budi@example.com',
     'jumlah': 2500, 'timestamp': '2025-02-05 11:45'},
    {'tipe': 'Transfer', 'member': 'Budi A. Santoso', 'email': 'budi@example.com',
     'jumlah': -2000, 'timestamp': '2025-02-10 14:00'},
    {'tipe': 'Package', 'member': 'John W. Doe', 'email': 'john@example.com',
     'jumlah': 10000, 'timestamp': '2025-03-01 08:00'},
]

TIER_CHOICES = ['Blue', 'Silver', 'Gold', 'Platinum']

def login_required_staf(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('role'):
            return redirect('accounts:login')
        if request.session.get('role') != 'staf':
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required_staf
def kelola_member_view(request):
    search = request.GET.get('q', '')
    filter_tier = request.GET.get('tier', 'Semua')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'tambah':
            new_member = {
                'nomor': f"M{len(DUMMY_MEMBERS) + 1:04d}",
                'nama': f"{request.POST.get('salutation')} {request.POST.get('first_mid_name')} {request.POST.get('last_name')}",
                'email': request.POST.get('email'),
                'tier': request.POST.get('tier', 'Blue'),
                'total_miles': 0,
                'award_miles': 0,
                'bergabung': date.today().strftime('%Y-%m-%d'),
            }
            DUMMY_MEMBERS.append(new_member)
            messages.success(request, 'Member baru berhasil ditambahkan.')

        elif action == 'edit':
            email = request.POST.get('email')

            for m in DUMMY_MEMBERS:
                if m['email'] == email:
                    m['nama'] = request.POST.get('nama')
                    m['tier'] = request.POST.get('tier')
                    m['total_miles'] = int(request.POST.get('total_miles', 0))
                    m['award_miles'] = int(request.POST.get('award_miles', 0))
                    break

            messages.success(request, f'Data member {email} berhasil diperbarui.')

        elif action == 'hapus':
            email = request.POST.get('email')

            for m in DUMMY_MEMBERS:
                if m['email'] == email:
                    DUMMY_MEMBERS.remove(m)
                    break

            messages.success(request, f'Member {email} berhasil dihapus.')

        return redirect('staff:kelola_member')

    members = DUMMY_MEMBERS

    if search:
        members = [
            m for m in members
            if search.lower() in m['nama'].lower()
            or search.lower() in m['email'].lower()
            or search.lower() in m['nomor'].lower()
        ]

    if filter_tier != 'Semua':
        members = [m for m in members if m['tier'] == filter_tier]

    paginator = Paginator(members, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'staff/kelola_member.html', {
        'members': page_obj,
        'page_obj': page_obj,
        'search': search,
        'filter_tier': filter_tier,
        'tier_choices': TIER_CHOICES,
    })

@login_required_staf
def dashboard(request):
    # Mengambil data dinamis dari session user yang sedang login
    # Gunakan .get() dan nilai default agar tidak error jika session kosong
    context = {
        'nama': request.session.get('nama', 'Nama Belum Diatur'),
        'email': request.session.get('email', 'Email Belum Diatur'),
        'telepon': request.session.get('mobile_number', '-'), 
        'kewarganegaraan': request.session.get('kewarganegaraan', 'Indonesia'),
        'tanggal_lahir': request.session.get('tanggal_lahir', '-'),

        # Stat Cards
        'nomor_member': request.session.get('nomor_member', 'Belum Ada'),
        'tier': request.session.get('tier', 'BLUE'),
        'total_miles': request.session.get('total_miles', 0),
        'award_miles': request.session.get('award_miles', 0),

        'transaksi': [
            {'tipe': 'Transfer', 'tanggal': '2026-04-26 10:31:20', 'miles': -1000},
            {'tipe': 'Redeem',   'tanggal': '2026-04-26 10:31:20', 'miles': -10000},
            {'tipe': 'Package',  'tanggal': '2026-04-26 10:31:20', 'miles': +16000},
            {'tipe': 'Package',  'tanggal': '2026-04-26 10:31:20', 'miles': +16000},
            {'tipe': 'Redeem',   'tanggal': '2026-04-26 10:31:20', 'miles': -10000},
        ],
    }
    return render(request, 'staff/dashboard.html', context)

from django.db import connection

# ... (Pastikan decorator @login_required_staf tetap ada)

@login_required_staf
def kelola_klaim_view(request):
    filter_status = request.GET.get('status', 'Semua')
    filter_maskapai = request.GET.get('maskapai', 'Semua')

    # logic update status yang akan membuat trigger terexecute
    if request.method == 'POST':
        action = request.POST.get('action')
        klaim_id = request.POST.get('klaim_id')

        # tentukan status baru berdasarkan tombol yang ditekan
        status_baru = 'Disetujui' if action == 'setujui' else 'Ditolak'

        try:
            # Dihapus transaction.atomic()-nya agar Supabase langsung auto-commit
            with connection.cursor() as cursor:
                if action == 'setujui':
                    # Explicit casting ::integer untuk mencegah id tidak terbaca
                    cursor.execute("""
                        UPDATE claim_missing_miles 
                        SET status_penerimaan = 'Disetujui', email_staf = %s 
                        WHERE id = %s::integer 
                        RETURNING email_member, flight_number
                    """, [email_staf, klaim_id])
                    
                    row = cursor.fetchone()
                    if row:
                        connection.commit()
                        email_member, flight_number = row
                        messages.success(request, f'SUKSES: Total miles Member "{email_member}" telah diperbarui. Miles ditambahkan: 1000 miles dari klaim penerbangan "{flight_number}".')
                    else:
                        messages.error(request, f"Gagal: Database menolak update. Klaim #{klaim_id} tidak ditemukan.")
                elif action == 'tolak':
                    cursor.execute("""
                        UPDATE claim_missing_miles 
                        SET status_penerimaan = 'Ditolak', email_staf = %s 
                        WHERE id = %s::integer
                    """, [email_staf, klaim_id])
                    
                    if cursor.rowcount > 0:
                        messages.success(request, f'SUKSES: Klaim #{klaim_id} telah ditolak.')
                    else:
                        messages.error(request, f"Gagal: Database menolak update. Klaim #{klaim_id} tidak ditemukan.")
                        
        except Exception as e:
            # Menangkap error trigger asli dari PostgreSQL
            pesan_error = str(e).split('\n')[0].strip()
            if "SUKSES:" in pesan_error:
                messages.success(request, pesan_error)
            elif "ERROR:" in pesan_error:
                messages.error(request, pesan_error)
            else:
                messages.error(request, f'Gagal memproses klaim: {pesan_error}')
            
        return redirect('staff:kelola_klaim')

    # Bagian bawah ini untuk menampilkan data ke tabel
    with connection.cursor() as cursor:
        query = """
            SELECT 
                c.id, p.first_mid_name || ' ' || p.last_name AS member_name, c.email_member AS email,
                c.maskapai, c.bandara_asal || ' → ' || c.bandara_tujuan AS rute,
                c.tanggal_penerbangan AS tanggal, c.flight_number AS flight,
                c.kelas_kabin AS kelas, c.timestamp AS timestamp, c.status_penerimaan AS status
            FROM claim_missing_miles c
            JOIN pengguna p ON c.email_member = p.email
            WHERE 1=1
        """
        params = []
        if filter_status != 'Semua':
            query += " AND c.status_penerimaan = %s"
            params.append(filter_status)
        if filter_maskapai != 'Semua':
            query += " AND c.maskapai = %s"
            params.append(filter_maskapai)
            
        query += " ORDER BY c.timestamp DESC"
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        # ubah hasil query menjadi list of dictionary agar mudah dibaca template html
        klaim_list = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, 'staff/kelola_klaim.html', {
        'klaim_list': klaim_list,
        'filter_status': filter_status,
        'filter_maskapai': filter_maskapai,
        'maskapai_list': ['GA', 'QG', 'JT', 'SQ', 'MH'], 
    })
@login_required_staf
def kelola_hadiah_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        kode = request.POST.get('kode_hadiah')

        if action == 'tambah':
            nama = request.POST.get('nama_reward')
            miles = request.POST.get('miles')
            deskripsi = request.POST.get('deskripsi', '')
            start = request.POST.get('valid_start')
            end = request.POST.get('program_end')
            penyedia_id = request.POST.get('penyedia_name')
            
            try:
                with connection.cursor() as cursor:
                    # cari angka ID terbesar (MAX), bukan di-COUNT, agar anti bentrok
                    cursor.execute("SELECT MAX(CAST(SUBSTRING(kode_hadiah FROM 5) AS INTEGER)) FROM hadiah")
                    max_id = cursor.fetchone()[0]
                    max_id = max_id if max_id is not None else 0
                    new_kode = f"RWD-{max_id + 1:03d}"
                    
                    cursor.execute("""
                        INSERT INTO hadiah (kode_hadiah, nama, miles, deskripsi, valid_start_date, program_end, id_penyedia)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, [new_kode, nama, miles, deskripsi, start, end, penyedia_id])
                    
                    # force commit ke Supabase
                    connection.commit()
                    
                messages.success(request, f'Hadiah berhasil ditambah dengan kode {new_kode}.')
            except Exception as e:
                # PERBAIKAN 3: Munculkan pesan error ASLI dari database agar kita tahu salahnya di mana
                messages.error(request, f'Gagal menambah hadiah: {str(e)}')

        elif action == 'edit':
            nama = request.POST.get('nama_reward')
            miles = request.POST.get('miles')
            deskripsi = request.POST.get('deskripsi', '')
            start = request.POST.get('valid_start')
            end = request.POST.get('program_end')
            penyedia_id = request.POST.get('penyedia_name')
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE hadiah
                        SET nama=%s, miles=%s, deskripsi=%s, valid_start_date=%s, program_end=%s, id_penyedia=%s
                        WHERE kode_hadiah=%s
                    """, [nama, miles, deskripsi, start, end, penyedia_id, kode])
                    connection.commit()
                messages.success(request, 'Detail hadiah berhasil diperbarui.')
            except Exception as e:
                messages.error(request, f'Gagal mengedit hadiah: {str(e)}')

        elif action == 'hapus':
            try:
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM hadiah WHERE kode_hadiah=%s", [kode])
                    connection.commit()
                messages.success(request, 'Hadiah berhasil dihapus.')
            except Exception as e:
                pass # Abaikan jika ada format tanggal yang aneh dari dummy

    return render(request, 'staff/kelola_hadiah.html', {
        'hadiah_list': DUMMY_HADIAH_STAF,
        'penyedia_choices': PENYEDIA_CHOICES,
    })

@login_required_staf
def kelola_mitra_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        email = request.POST.get('email_mitra')

        if action == 'tambah':
            # Logika: Otomatis buat entri PENYEDIA baru (Simulasi ID)
            new_id = len(DUMMY_MITRA) + 5
            DUMMY_MITRA.append({
                'email': email,
                'id_penyedia': new_id,
                'nama': request.POST.get('nama_mitra'),
                'tanggal': request.POST.get('tanggal_kerja_sama'),
            })
            messages.success(request, f'Mitra baru berhasil didaftarkan!')

        elif action == 'edit':
            # update data kecuali Email (PK) dan ID Penyedia
            for m in DUMMY_MITRA:
                if m['email'] == email:
                    m['nama'] = request.POST.get('nama_mitra')
                    m['tanggal'] = request.POST.get('tanggal_kerja_sama')
            messages.success(request, 'Informasi mitra berhasil diperbarui.')

        elif action == 'hapus':
            email_hapus = request.POST.get('email_mitra')
            
            # cari nama mitra yang akan dihapus 
            nama_mitra = None
            for m in DUMMY_MITRA:
                if m['email'] == email_hapus:
                    nama_mitra = m['nama']
                    break
            
            # hapus Mitra dari daftar
            for i, m in enumerate(DUMMY_MITRA):
                if m['email'] == email_hapus:
                    DUMMY_MITRA.pop(i)
                    break
            
            # hapus Hadiah yang dimiliki oleh Mitra tersebut (jika ada)
            if nama_mitra:
                global DUMMY_HADIAH_STAF
                DUMMY_HADIAH_STAF = [h for h in DUMMY_HADIAH_STAF if h.get('penyedia') != nama_mitra]

            messages.warning(request, 'Mitra dan seluruh hadiah terkait berhasil dihapus.')

        return redirect('staff:kelola_mitra')

    return render(request, 'staff/kelola_mitra.html', {'mitra_list': DUMMY_MITRA})



def login_required_staf(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('role'):
            return redirect('accounts:login')
        if request.session.get('role') != 'staf':
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required_staf
def laporan_view(request):
    filter_tipe = request.GET.get('tipe', 'Semua')
    active_tab  = request.GET.get('tab', 'riwayat')

    transaksi = []

    if filter_tipe in ('Semua', 'Redeem'):
        with connection.cursor() as cur:
            cur.execute("""
                SELECT r.timestamp, p.first_mid_name || ' ' || p.last_name AS member, r.email_member AS email,
                       'Redeem' AS tipe, -h.miles AS jumlah
                FROM redeem r JOIN hadiah h ON h.kode_hadiah = r.kode_hadiah JOIN pengguna p ON p.email = r.email_member
                ORDER BY r.timestamp DESC
            """)
            cols = [c.name for c in cur.description]
            transaksi += [dict(zip(cols, row)) for row in cur.fetchall()]

    if filter_tipe in ('Semua', 'Package'):
        with connection.cursor() as cur:
            cur.execute("""
                SELECT mp.timestamp, p.first_mid_name || ' ' || p.last_name AS member, mp.email_member AS email,
                       'Package' AS tipe, ap.jumlah_award_miles AS jumlah
                FROM member_award_miles_package mp JOIN award_miles_package ap ON ap.id = mp.id_award_miles_package JOIN pengguna p ON p.email = mp.email_member
                ORDER BY mp.timestamp DESC
            """)
            cols = [c.name for c in cur.description]
            transaksi += [dict(zip(cols, row)) for row in cur.fetchall()]

    if filter_tipe in ('Semua', 'Transfer'):
        with connection.cursor() as cur:
            cur.execute("""
                SELECT t.timestamp, p.first_mid_name || ' ' || p.last_name AS member, t.email_member_1 AS email,
                       'Transfer' AS tipe, -t.jumlah AS jumlah
                FROM transfer t JOIN pengguna p ON p.email = t.email_member_1
                ORDER BY t.timestamp DESC
            """)
            cols = [c.name for c in cur.description]
            transaksi += [dict(zip(cols, row)) for row in cur.fetchall()]

    if filter_tipe in ('Semua', 'Klaim'):
        with connection.cursor() as cur:
            cur.execute("""
                SELECT c.timestamp, p.first_mid_name || ' ' || p.last_name AS member, c.email_member AS email,
                       'Klaim' AS tipe, 0 AS jumlah
                FROM claim_missing_miles c JOIN pengguna p ON p.email = c.email_member
                ORDER BY c.timestamp DESC
            """)
            cols = [c.name for c in cur.description]
            transaksi += [dict(zip(cols, row)) for row in cur.fetchall()]

    transaksi.sort(key=lambda x: x['timestamp'], reverse=True)

    with connection.cursor() as cur:
        cur.execute("SELECT COALESCE(SUM(award_miles), 0) FROM member")
        total_miles_beredar = cur.fetchone()[0]

    today = date.today()
    with connection.cursor() as cur:
        cur.execute("""
            SELECT COALESCE(SUM(h.miles), 0) FROM redeem r JOIN hadiah h ON h.kode_hadiah = r.kode_hadiah
            WHERE EXTRACT(MONTH FROM r.timestamp) = %s AND EXTRACT(YEAR FROM r.timestamp) = %s
        """, [today.month, today.year])
        total_redeem_bulan_ini = cur.fetchone()[0]

    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM claim_missing_miles WHERE status_penerimaan = 'Disetujui'")
        total_klaim_disetujui = cur.fetchone()[0]

    # MENGEMBALIKAN FUNGSI STORED PROCEDURE TOP 5 MEMBER
    with connection.cursor() as cur:
        try:
            cur.execute("SELECT * FROM get_top_5_members()")
            cols = [c.name for c in cur.description]
            raw_top_members = cur.fetchall()
            
            if raw_top_members:
                top_members = [dict(zip(cols, row)) for row in raw_top_members]
                pesan_prosedur = top_members[0].get('pesan_sukses', '')
                if pesan_prosedur:
                    messages.success(request, pesan_prosedur)
            else:
                top_members = []
        except Exception as e:
            top_members = []
            messages.error(request, f'Gagal memuat Top 5 Member: {str(e)}')

    return render(request, 'staff/laporan.html', {
        'transaksi': transaksi,
        'filter_tipe': filter_tipe,
        'active_tab': active_tab,
        'total_miles_beredar': total_miles_beredar,
        'total_redeem_bulan_ini': total_redeem_bulan_ini,
        'total_klaim_disetujui': total_klaim_disetujui,
        'top_members': top_members,
    })