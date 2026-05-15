from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.contrib.auth.hashers import make_password
from datetime import date
from django.core.paginator import Paginator

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
            with connection.cursor() as cursor:
                # raw query untuk mengupdate status
                cursor.execute("""
                    UPDATE CLAIM_MISSING_MILES
                    SET status_penerimaan = %s
                    WHERE id = %s
                """, [status_baru, klaim_id])
            
            # jika aksi Ditolak (tidak memicu exception trigger)
            if action == 'tolak':
                messages.warning(request, f'Klaim {klaim_id} telah ditolak.')
                
        except Exception as e:
            # menangkap pesan EXCEPTION langsung dari Trigger PostgreSQL
            pesan_trigger = str(e).split('\n')[0].strip() # Ambil baris pertama saja
            
            # karena trigger mengirim text berawalan "SUKSES:", kita parse pesannya
            if "SUKSES:" in pesan_trigger:
                pesan_bersih = pesan_trigger.replace('SUKSES: ', '')
                messages.success(request, pesan_bersih)
            else:
                messages.error(request, pesan_trigger)

        return redirect('staff:kelola_klaim')

    # logic untuk ambil data claim
    klaim_list = []
    
    # membuat filter query secara dinamis
    where_clauses = []
    params = []
    
    if filter_status != 'Semua':
        where_clauses.append("c.status_penerimaan = %s")
        params.append(filter_status)
    if filter_maskapai != 'Semua':
        where_clauses.append("m.kode_maskapai = %s")
        params.append(filter_maskapai)
        
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    query = f"""
        SELECT 
            c.id, 
            p.first_mid_name || ' ' || p.last_name AS member, 
            c.email_member AS email,
            m.kode_maskapai AS maskapai, 
            c.bandara_asal || ' → ' || c.bandara_tujuan AS rute, 
            c.tanggal_penerbangan AS tanggal,
            c.flight_number AS flight, 
            c.kelas_kabin AS kelas, 
            c.timestamp AS pengajuan, 
            c.status_penerimaan AS status
        FROM CLAIM_MISSING_MILES c
        JOIN PENGGUNA p ON c.email_member = p.email
        JOIN MASKAPAI m ON c.maskapai = m.kode_maskapai
        {where_sql}
        ORDER BY c.timestamp DESC
    """

    with connection.cursor() as cursor:
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
            # Generate Kode Otomatis
            new_kode = f"RWD-00{len(DUMMY_HADIAH_STAF) + 1}"
            
            # Gabungkan start dan end menjadi format 'periode'
            start = request.POST.get('valid_start')
            end = request.POST.get('program_end')
            periode_str = f"{start} — {end}"
            
            DUMMY_HADIAH_STAF.append({
                'kode': new_kode,
                'nama': request.POST.get('nama_reward'),
                'miles': int(request.POST.get('miles')),
                'deskripsi': request.POST.get('deskripsi'),
                'periode': periode_str, # Simpan dalam format dummy asli
                'penyedia': request.POST.get('penyedia_name'), 
                'tipe_penyedia': 'partner', # default simulasi
                'aktif': True
            })
            messages.success(request, f'Hadiah berhasil ditambah dengan kode {new_kode}.')

        elif action == 'edit':
            # Kode Hadiah tidak dapat diubah
            for h in DUMMY_HADIAH_STAF:
                if h['kode'] == kode:
                    h['nama'] = request.POST.get('nama_reward')
                    h['miles'] = int(request.POST.get('miles'))
                    h['penyedia'] = request.POST.get('penyedia_name')
                    h['deskripsi'] = request.POST.get('deskripsi')
                    
                    # Gabungkan start dan end kembali
                    start = request.POST.get('valid_start')
                    end = request.POST.get('program_end')
                    h['periode'] = f"{start} — {end}"
            messages.success(request, 'Detail hadiah berhasil diperbarui.')

        elif action == 'hapus':
            # hanya bisa hapus kalau periode sudah selesai (aktif=False)
            hadiah = next((h for h in DUMMY_HADIAH_STAF if h['kode'] == kode), None)
            if hadiah and not hadiah['aktif']:
                for i, h in enumerate(DUMMY_HADIAH_STAF):
                    if h['kode'] == kode:
                        DUMMY_HADIAH_STAF.pop(i)
                        break
                messages.success(request, 'Hadiah yang sudah tidak berlaku berhasil dihapus.')
            else:
                messages.error(request, 'Gagal! Hadiah masih aktif dan tidak dapat dihapus.')

        return redirect('staff:kelola_hadiah') # Typo 'ke1lola_hadiah' sudah diperbaiki
    
    today = datetime.now().date()
    for h in DUMMY_HADIAH_STAF:
        if 'periode' in h:
            try:
                # memecah string '2024-01-01 — 2025-12-31' menjadi dua bagian
                parts = h['periode'].replace(' - ', ' — ').split(' — ')
                if len(parts) == 2:
                    start_str = parts[0].strip()
                    end_str = parts[1].strip()
                    
                    h['valid_start'] = start_str
                    h['program_end'] = end_str
                    
                    # Cek aktif/selesai berdasarkan tanggal end
                    end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
                    h['aktif'] = end_date >= today
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

    # ── Redeem ───────────────────────────────────────────────
    if filter_tipe in ('Semua', 'Redeem'):
        with connection.cursor() as cur:
            cur.execute("""
                SELECT
                    r.timestamp,
                    p.first_mid_name || ' ' || p.last_name AS member,
                    r.email_member                          AS email,
                    'Redeem'                                AS tipe,
                    -h.miles                                AS jumlah
                FROM redeem r
                JOIN hadiah h   ON h.kode_hadiah = r.kode_hadiah
                JOIN pengguna p ON p.email = r.email_member
                ORDER BY r.timestamp DESC
            """)
            cols = [c.name for c in cur.description]
            transaksi += [dict(zip(cols, row)) for row in cur.fetchall()]

    # ── Package ──────────────────────────────────────────────
    if filter_tipe in ('Semua', 'Package'):
        with connection.cursor() as cur:
            cur.execute("""
                SELECT
                    mp.timestamp,
                    p.first_mid_name || ' ' || p.last_name AS member,
                    mp.email_member                         AS email,
                    'Package'                               AS tipe,
                    ap.jumlah_award_miles                   AS jumlah
                FROM member_award_miles_package mp
                JOIN award_miles_package ap ON ap.id = mp.id_award_miles_package
                JOIN pengguna p             ON p.email = mp.email_member
                ORDER BY mp.timestamp DESC
            """)
            cols = [c.name for c in cur.description]
            transaksi += [dict(zip(cols, row)) for row in cur.fetchall()]

    # ── Transfer ─────────────────────────────────────────────
    if filter_tipe in ('Semua', 'Transfer'):
        with connection.cursor() as cur:
            cur.execute("""
                SELECT
                    t.timestamp,
                    p.first_mid_name || ' ' || p.last_name AS member,
                    t.email_member_1                        AS email,
                    'Transfer'                              AS tipe,
                    -t.jumlah                               AS jumlah
                FROM transfer t
                JOIN pengguna p ON p.email = t.email_member_1
                ORDER BY t.timestamp DESC
            """)
            cols = [c.name for c in cur.description]
            transaksi += [dict(zip(cols, row)) for row in cur.fetchall()]

    # ── Klaim ────────────────────────────────────────────────
    if filter_tipe in ('Semua', 'Klaim'):
        with connection.cursor() as cur:
            cur.execute("""
                SELECT
                    c.timestamp,
                    p.first_mid_name || ' ' || p.last_name AS member,
                    c.email_member                          AS email,
                    'Klaim'                                 AS tipe,
                    0                                       AS jumlah
                FROM claim_missing_miles c
                JOIN pengguna p ON p.email = c.email_member
                ORDER BY c.timestamp DESC
            """)
            cols = [c.name for c in cur.description]
            transaksi += [dict(zip(cols, row)) for row in cur.fetchall()]

    # Urutkan semua dari terbaru
    transaksi.sort(key=lambda x: x['timestamp'], reverse=True)

    # ── Stat cards ───────────────────────────────────────────
    # Total miles beredar = sum award_miles semua member
    with connection.cursor() as cur:
        cur.execute("SELECT COALESCE(SUM(award_miles), 0) FROM member")
        total_miles_beredar = cur.fetchone()[0]

    # Total redeem bulan ini (dalam miles)
    today = date.today()
    with connection.cursor() as cur:
        cur.execute("""
            SELECT COALESCE(SUM(h.miles), 0)
            FROM redeem r
            JOIN hadiah h ON h.kode_hadiah = r.kode_hadiah
            WHERE EXTRACT(MONTH FROM r.timestamp) = %s
              AND EXTRACT(YEAR  FROM r.timestamp) = %s
        """, [today.month, today.year])
        total_redeem_bulan_ini = cur.fetchone()[0]

    # Total klaim disetujui
    with connection.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM claim_missing_miles WHERE status_penerimaan = 'Disetujui'"
        )
        total_klaim_disetujui = cur.fetchone()[0]

    # ── Top members ──────────────────────────────────────────
    with connection.cursor() as cur:
        # panggil Stored Procedure (Function) yang sudah dibuat di Supabase
        cur.execute("SELECT * FROM get_top_5_members()")
        cols = [c.name for c in cur.description]
        
        # ambil semua datanya
        raw_top_members = cur.fetchall()
        
        if raw_top_members:
            # ubah jadi list of dictionary agar gampang dibaca HTML
            top_members = [dict(zip(cols, row)) for row in raw_top_members]
            
            # ambil pesan_sukses dari baris pertama data (karena pesannya sama di semua baris)
            pesan_prosedur = top_members[0]['pesan_sukses']
            
            # tampilkan pesan ke toast django
            messages.success(request, pesan_prosedur)
        else:
            top_members = []

    return render(request, 'staff/laporan.html', {
        'transaksi'             : transaksi,
        'filter_tipe'           : filter_tipe,
        'active_tab'            : active_tab,
        'total_miles_beredar'   : total_miles_beredar,
        'total_redeem_bulan_ini': total_redeem_bulan_ini,
        'total_klaim_disetujui' : total_klaim_disetujui,
        'top_members'           : top_members,
    })