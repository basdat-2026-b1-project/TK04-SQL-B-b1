from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.contrib.auth.hashers import make_password
from datetime import date
from django.core.paginator import Paginator

from member.views import login_required_member

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

    tier_map = {'Blue': 'T01', 'Silver': 'T02', 'Gold': 'T03', 'Platinum': 'T04'}

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'tambah':
            email = request.POST.get('email')
            password = request.POST.get('password')
            salutation = request.POST.get('salutation')
            first_mid_name = request.POST.get('first_mid_name')
            last_name = request.POST.get('last_name')
            country_code = request.POST.get('country_code')
            mobile_number = request.POST.get('mobile_number')
            tanggal_lahir = request.POST.get('tanggal_lahir')
            kewarganegaraan = request.POST.get('kewarganegaraan')
            tier_name = request.POST.get('tier', 'Blue')
            id_tier = tier_map.get(tier_name, 'T01')
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO pengguna (email, password, salutation, first_mid_name, last_name, country_code, mobile_number, tanggal_lahir, kewarganegaraan)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [email, password, salutation, first_mid_name, last_name, country_code, mobile_number, tanggal_lahir, kewarganegaraan])
                    
                    cursor.execute("SELECT COUNT(*) FROM member")
                    count = cursor.fetchone()[0]
                    nomor_member = f"M{count + 1:04d}"
                    
                    cursor.execute("""
                        INSERT INTO member (email, nomor_member, tanggal_bergabung, id_tier, award_miles, total_miles)
                        VALUES (%s, %s, CURRENT_DATE, %s, 0, 0)
                    """, [email, nomor_member, id_tier])
                    
                messages.success(request, 'Member baru berhasil ditambahkan.')
            except Exception as e:
                messages.error(request, f'Gagal menambahkan member: {str(e)}')

        elif action == 'edit':
            email = request.POST.get('email')
            nama = request.POST.get('nama', '')
            tier_name = request.POST.get('tier', 'Blue')
            id_tier = tier_map.get(tier_name, 'T01')
            total_miles = request.POST.get('total_miles', 0)
            award_miles = request.POST.get('award_miles', 0)
            
            parts = nama.split(' ')
            salutation = parts[0] if parts and parts[0] in ['Mr.', 'Mrs.', 'Ms.', 'Dr.'] else ''
            if salutation:
                parts = parts[1:]
            
            first_mid = parts[0] if len(parts) > 0 else ''
            last = ' '.join(parts[1:]) if len(parts) > 1 else ''
            
            try:
                with connection.cursor() as cursor:
                    if salutation:
                        cursor.execute("""
                            UPDATE pengguna
                            SET salutation = %s, first_mid_name = %s, last_name = %s
                            WHERE email = %s
                        """, [salutation, first_mid, last, email])
                    else:
                        cursor.execute("""
                            UPDATE pengguna
                            SET first_mid_name = %s, last_name = %s
                            WHERE email = %s
                        """, [first_mid, last, email])
                        
                    cursor.execute("""
                        UPDATE member
                        SET id_tier = %s, total_miles = %s, award_miles = %s
                        WHERE email = %s
                    """, [id_tier, total_miles, award_miles, email])
                messages.success(request, f'Data member {email} berhasil diperbarui.')
            except Exception as e:
                messages.error(request, f'Gagal mengedit member: {str(e)}')

        elif action == 'hapus':
            email = request.POST.get('email')
            try:
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM pengguna WHERE email = %s", [email])
                messages.success(request, f'Member {email} berhasil dihapus.')
            except Exception as e:
                messages.error(request, f'Gagal menghapus member: {str(e)}')

        return redirect('staff:kelola_member')

    with connection.cursor() as cursor:
        query = """
            SELECT 
                m.nomor_member AS nomor,
                p.salutation || ' ' || p.first_mid_name || ' ' || p.last_name AS nama,
                m.email,
                t.nama AS tier,
                m.total_miles,
                m.award_miles,
                m.tanggal_bergabung AS bergabung
            FROM member m
            JOIN pengguna p ON m.email = p.email
            JOIN tier t ON m.id_tier = t.id_tier
            WHERE 1=1
        """
        params = []
        if search:
            query += " AND (LOWER(p.first_mid_name || ' ' || p.last_name) LIKE %s OR LOWER(m.email) LIKE %s OR LOWER(m.nomor_member) LIKE %s)"
            search_param = f"%{search.lower()}%"
            params.extend([search_param, search_param, search_param])
        
        if filter_tier != 'Semua':
            query += " AND t.nama = %s"
            params.append(filter_tier)
            
        query += " ORDER BY m.nomor_member ASC"
        cursor.execute(query, params)
        
        cols = [col[0] for col in cursor.description]
        members = [dict(zip(cols, row)) for row in cursor.fetchall()]

        cursor.execute("SELECT nama FROM tier ORDER BY minimal_tier_miles ASC")
        tier_choices = [row[0] for row in cursor.fetchall()]

    paginator = Paginator(members, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'staff/kelola_member.html', {
        'members': page_obj,
        'page_obj': page_obj,
        'search': search,
        'filter_tier': filter_tier,
        'tier_choices': tier_choices,
    })

@login_required_staf
def dashboard(request):
    context = {
        'nama': request.session.get('nama', 'Nama Belum Diatur'),
        'email': request.session.get('email', 'Email Belum Diatur'),
        'telepon': request.session.get('mobile_number', '-'), 
        'kewarganegaraan': request.session.get('kewarganegaraan', 'Indonesia'),
        'tanggal_lahir': request.session.get('tanggal_lahir', '-'),
    }
    
    with connection.cursor() as cursor:
        query = """
            SELECT tipe, timestamp, miles FROM (
                SELECT 'Transfer' AS tipe, timestamp, jumlah AS miles FROM transfer
                UNION ALL
                SELECT 'Redeem' AS tipe, timestamp, -h.miles AS miles FROM redeem r JOIN hadiah h ON r.kode_hadiah = h.kode_hadiah
                UNION ALL
                SELECT 'Package' AS tipe, timestamp, p.jumlah_award_miles AS miles FROM member_award_miles_package mp JOIN award_miles_package p ON mp.id_award_miles_package = p.id
            ) t
            ORDER BY timestamp DESC LIMIT 5
        """
        cursor.execute(query)
        cols = [col[0] for col in cursor.description]
        context['transaksi'] = [dict(zip(cols, row)) for row in cursor.fetchall()]

    return render(request, 'staff/dashboard.html', context)

@login_required_staf
def laporan_transaksi_view(request):
    active_tab = request.GET.get('tab', 'riwayat')
    filter_tipe = request.GET.get('tipe', 'Semua')

    if request.method == 'POST':
        pass

    with connection.cursor() as cursor:
        cursor.execute("SELECT COALESCE(SUM(total_miles), 0) FROM member")
        total_miles_beredar = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(h.miles), 0) FROM redeem r JOIN hadiah h ON r.kode_hadiah = h.kode_hadiah WHERE EXTRACT(MONTH FROM r.timestamp) = EXTRACT(MONTH FROM CURRENT_DATE)")
        total_redeem_bulan_ini = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM claim_missing_miles WHERE status_penerimaan = 'Disetujui'")
        total_klaim_disetujui = cursor.fetchone()[0]

        query = """
            SELECT tipe, email, member, jumlah, timestamp FROM (
                SELECT 'Transfer' AS tipe, t.email_member_1 AS email, p1.first_mid_name || ' ' || p1.last_name AS member, -t.jumlah AS jumlah, t.timestamp 
                FROM transfer t JOIN pengguna p1 ON t.email_member_1 = p1.email
                UNION ALL
                SELECT 'Redeem' AS tipe, r.email_member AS email, p2.first_mid_name || ' ' || p2.last_name AS member, -h.miles AS jumlah, r.timestamp 
                FROM redeem r JOIN hadiah h ON r.kode_hadiah = h.kode_hadiah JOIN pengguna p2 ON r.email_member = p2.email
                UNION ALL
                SELECT 'Package' AS tipe, mp.email_member AS email, p3.first_mid_name || ' ' || p3.last_name AS member, pkg.jumlah_award_miles AS jumlah, mp.timestamp 
                FROM member_award_miles_package mp JOIN award_miles_package pkg ON mp.id_award_miles_package = pkg.id JOIN pengguna p3 ON mp.email_member = p3.email
            ) t
            WHERE 1=1
        """
        params = []
        if filter_tipe != 'Semua' and filter_tipe != 'Klaim':
            query += " AND tipe = %s"
            params.append(filter_tipe)
            
        query += " ORDER BY timestamp DESC"
        cursor.execute(query, params)
        cols = [col[0] for col in cursor.description]
        transaksi = [dict(zip(cols, row)) for row in cursor.fetchall()]

        cursor.execute("""
            SELECT 
                p.first_mid_name || ' ' || p.last_name AS member,
                m.email,
                m.total_miles,
                (SELECT COUNT(*) FROM transfer WHERE email_member_1 = m.email OR email_member_2 = m.email) +
                (SELECT COUNT(*) FROM redeem WHERE email_member = m.email) +
                (SELECT COUNT(*) FROM member_award_miles_package WHERE email_member = m.email) AS jumlah_transaksi
            FROM member m
            JOIN pengguna p ON m.email = p.email
            ORDER BY m.total_miles DESC
            LIMIT 3
        """)
        cols = [col[0] for col in cursor.description]
        top_members = [dict(zip(cols, row)) for row in cursor.fetchall()]

    return render(request, 'staff/laporan.html', {
        'total_miles_beredar': total_miles_beredar,
        'total_redeem_bulan_ini': total_redeem_bulan_ini,
        'total_klaim_disetujui': total_klaim_disetujui,
        'active_tab': active_tab,
        'filter_tipe': filter_tipe,
        'transaksi': transaksi,
        'top_members': top_members,
    })


def _apply_filters(query: str, params: list, mulai: str, akhir: str, email: str):
    """Tambahkan klausa WHERE umum (tanggal & email) ke query."""
    if email:
        query  += " AND r.email_member = %s" if 'r.email_member' in query else " AND mp.email_member = %s"
        params += [email]
    if mulai:
        query  += " AND r.timestamp >= %s" if 'r.timestamp' in query else " AND mp.timestamp >= %s"
        params += [mulai]
    if akhir:
        query  += " AND r.timestamp <= %s" if 'r.timestamp' in query else " AND mp.timestamp <= %s"
        params += [akhir + ' 23:59:59']
    return query, params


@login_required_staf
def kelola_klaim_view(request):
    filter_status = request.GET.get('status', 'Semua')
    filter_maskapai = request.GET.get('maskapai', 'Semua')
    email_staf = request.session.get('email')

    if request.method == 'POST':
        action = request.POST.get('action')
        klaim_id = request.POST.get('klaim_id')
        
        try:
            with connection.cursor() as cursor:
                if action == 'setujui':
                    cursor.execute("UPDATE claim_missing_miles SET status_penerimaan = 'Disetujui', email_staf = %s WHERE id = %s", [email_staf, klaim_id])
                    messages.success(request, f'Klaim {klaim_id} berhasil disetujui. Miles ditambahkan ke akun member.')
                elif action == 'tolak':
                    cursor.execute("UPDATE claim_missing_miles SET status_penerimaan = 'Ditolak', email_staf = %s WHERE id = %s", [email_staf, klaim_id])
                    messages.warning(request, f'Klaim {klaim_id} telah ditolak.')
        except Exception as e:
            messages.error(request, f'Gagal memproses klaim: {str(e)}')
            
        return redirect('staff:kelola_klaim')

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
        cols = [col[0] for col in cursor.description]
        klaim_list = [dict(zip(cols, row)) for row in cursor.fetchall()]

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
            deskripsi = request.POST.get('deskripsi')
            start = request.POST.get('valid_start')
            end = request.POST.get('program_end')
            penyedia_id = request.POST.get('penyedia_name')
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM hadiah")
                    new_kode = f"RWD-{cursor.fetchone()[0] + 1:03d}"
                    
                    cursor.execute("""
                        INSERT INTO hadiah (kode_hadiah, nama, miles, deskripsi, valid_start_date, program_end, id_penyedia)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, [new_kode, nama, miles, deskripsi, start, end, penyedia_id])
                messages.success(request, f'Hadiah berhasil ditambah dengan kode {new_kode}.')
            except Exception as e:
                messages.error(request, 'Gagal menambah hadiah karena format input tidak valid atau ada data yang kosong.')

        elif action == 'edit':
            nama = request.POST.get('nama_reward')
            miles = request.POST.get('miles')
            deskripsi = request.POST.get('deskripsi')
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
                messages.success(request, 'Detail hadiah berhasil diperbarui.')
            except Exception as e:
                messages.error(request, 'Gagal mengedit hadiah karena format input tidak valid atau penyedia tidak ditemukan.')

        elif action == 'hapus':
            try:
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM hadiah WHERE kode_hadiah=%s", [kode])
                messages.success(request, 'Hadiah berhasil dihapus.')
            except Exception as e:
                messages.error(request, f'Gagal menghapus hadiah: {str(e)}')

        return redirect('staff:kelola_hadiah')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT h.kode_hadiah AS kode, h.nama, h.deskripsi, h.miles, 
                   h.valid_start_date AS valid_start, h.program_end,
                   h.id_penyedia,
                   COALESCE(m.nama_mitra, ma.nama_maskapai) AS penyedia,
                   CASE WHEN m.nama_mitra IS NOT NULL THEN 'partner' ELSE 'airline' END AS tipe_penyedia,
                   CASE WHEN h.program_end >= CURRENT_DATE THEN TRUE ELSE FALSE END AS aktif
            FROM hadiah h
            LEFT JOIN mitra m ON h.id_penyedia = m.id_penyedia
            LEFT JOIN maskapai ma ON h.id_penyedia = ma.id_penyedia
            ORDER BY h.kode_hadiah ASC
        """)
        cols = [col[0] for col in cursor.description]
        hadiah_list = [dict(zip(cols, row)) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT id_penyedia, nama_mitra AS nama FROM mitra
            UNION
            SELECT id_penyedia, nama_maskapai AS nama FROM maskapai
        """)
        penyedia_choices = cursor.fetchall()

    return render(request, 'staff/kelola_hadiah.html', {
        'hadiah_list': hadiah_list,
        'penyedia_choices': penyedia_choices,
    })

@login_required_staf
def kelola_mitra_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        email = request.POST.get('email_mitra')

        if action == 'tambah':
            nama = request.POST.get('nama_mitra')
            tanggal = request.POST.get('tanggal_kerja_sama')
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute("INSERT INTO penyedia DEFAULT VALUES RETURNING id")
                    new_id = cursor.fetchone()[0]
                    
                    cursor.execute("""
                        INSERT INTO mitra (email_mitra, id_penyedia, nama_mitra, tanggal_kerja_sama)
                        VALUES (%s, %s, %s, %s)
                    """, [email, new_id, nama, tanggal])
                messages.success(request, 'Mitra baru berhasil didaftarkan!')
            except Exception as e:
                messages.error(request, f'Gagal menambah mitra: {str(e)}')

        elif action == 'edit':
            nama = request.POST.get('nama_mitra')
            tanggal = request.POST.get('tanggal_kerja_sama')
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE mitra SET nama_mitra=%s, tanggal_kerja_sama=%s WHERE email_mitra=%s
                    """, [nama, tanggal, email])
                messages.success(request, 'Informasi mitra berhasil diperbarui.')
            except Exception as e:
                messages.error(request, f'Gagal mengedit mitra: {str(e)}')

        elif action == 'hapus':
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT id_penyedia FROM mitra WHERE email_mitra=%s", [email])
                    row = cursor.fetchone()
                    if row:
                        id_penyedia = row[0]
                        cursor.execute("DELETE FROM mitra WHERE email_mitra=%s", [email])
                        cursor.execute("DELETE FROM penyedia WHERE id=%s", [id_penyedia])
                messages.warning(request, 'Mitra dan seluruh hadiah terkait berhasil dihapus.')
            except Exception as e:
                messages.error(request, f'Gagal menghapus mitra: {str(e)}')

        return redirect('staff:kelola_mitra')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT email_mitra AS email, id_penyedia, nama_mitra AS nama, tanggal_kerja_sama AS tanggal
            FROM mitra
        """)
        cols = [col[0] for col in cursor.description]
        mitra_list = [dict(zip(cols, row)) for row in cursor.fetchall()]

    return render(request, 'staff/kelola_mitra.html', {'mitra_list': mitra_list})
