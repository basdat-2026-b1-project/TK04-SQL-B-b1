from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.humanize.templatetags.humanize import intcomma
from datetime import date
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db import connection, transaction
from datetime import date

def login_required_member(view_func):
    """Simple decorator untuk cek session member"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('role'):
            return redirect('accounts:login')
        if request.session.get('role') != 'member':
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required_member
def identitas_view(request):
    email = request.session.get('email')
    
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'tambah':
            nomor = request.POST.get('nomor')
            jenis = request.POST.get('jenis')
            negara = request.POST.get('negara')
            tanggal_terbit = request.POST.get('tanggal_terbit')
            tanggal_habis = request.POST.get('tanggal_habis')
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1 FROM identitas WHERE nomor = %s", [nomor])
                    if cursor.fetchone():
                        messages.error(request, 'Nomor dokumen sudah terdaftar.')
                    else:
                        cursor.execute("""
                            INSERT INTO identitas (nomor, email_member, tanggal_habis, tanggal_terbit, negara_penerbit, jenis)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, [nomor, email, tanggal_habis, tanggal_terbit, negara, jenis])
                        messages.success(request, 'Identitas berhasil ditambahkan.')
            except Exception as e:
                messages.error(request, f'Gagal menambah identitas: {str(e)}')

        elif action == 'edit':
            nomor = request.POST.get('nomor')
            jenis = request.POST.get('jenis')
            negara = request.POST.get('negara')
            tanggal_terbit = request.POST.get('tanggal_terbit')
            tanggal_habis = request.POST.get('tanggal_habis')

            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE identitas
                        SET jenis=%s, negara_penerbit=%s, tanggal_terbit=%s, tanggal_habis=%s
                        WHERE nomor=%s AND email_member=%s
                    """, [jenis, negara, tanggal_terbit, tanggal_habis, nomor, email])
                messages.success(request, 'Identitas berhasil diperbarui.')
            except Exception as e:
                messages.error(request, f'Gagal mengedit identitas: {str(e)}')

        elif action == 'hapus':
            nomor = request.POST.get('nomor')
            try:
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM identitas WHERE nomor=%s AND email_member=%s", [nomor, email])
                messages.success(request, 'Identitas berhasil dihapus.')
            except Exception as e:
                messages.error(request, f'Gagal menghapus identitas: {str(e)}')

        return redirect('member:identitas')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT nomor, jenis, negara_penerbit AS negara, tanggal_terbit, tanggal_habis,
            CASE WHEN tanggal_habis >= CURRENT_DATE THEN 'Aktif' ELSE 'Kedaluwarsa' END AS status
            FROM identitas
            WHERE email_member = %s
        """, [email])
        cols = [col[0] for col in cursor.description]
        identitas_list = [dict(zip(cols, row)) for row in cursor.fetchall()]

    return render(request, 'member/identitas.html', {
        'identitas_list': identitas_list,
    })

@login_required_member
def claim_list(request):
    filter_status = request.GET.get('status', 'Semua')
    email = request.session.get('email')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'ajukan':
            maskapai = request.POST.get('maskapai')
            kelas = request.POST.get('kelas')
            asal = request.POST.get('asal')
            tujuan = request.POST.get('tujuan')
            tanggal = request.POST.get('tanggal')
            flight_number = request.POST.get('flight_number')
            nomor_tiket = request.POST.get('nomor_tiket')
            pnr = request.POST.get('pnr')

            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO claim_missing_miles 
                        (email_member, maskapai, bandara_asal, bandara_tujuan, tanggal_penerbangan, flight_number, nomor_tiket, pnr, kelas_kabin, status_penerimaan, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Menunggu', CURRENT_TIMESTAMP)
                    """, [email, maskapai, asal, tujuan, tanggal, flight_number, nomor_tiket, pnr, kelas])
                    
                messages.success(request, 'Klaim berhasil diajukan!')
            except Exception as e:
                messages.error(request, f'Gagal mengajukan klaim: {str(e)}')
            return redirect('member:claim_list')
        
        elif action == 'edit':
            klaim_id = request.POST.get('klaim_id')
            status_klaim = request.POST.get('status_saat_ini') 
            if status_klaim == 'Menunggu':
                maskapai = request.POST.get('maskapai')
                kelas = request.POST.get('kelas')
                asal = request.POST.get('asal')
                tujuan = request.POST.get('tujuan')
                tanggal = request.POST.get('tanggal')
                flight_number = request.POST.get('flight_number')
                nomor_tiket = request.POST.get('nomor_tiket')
                pnr = request.POST.get('pnr')
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE claim_missing_miles
                            SET maskapai=%s, bandara_asal=%s, bandara_tujuan=%s, tanggal_penerbangan=%s, flight_number=%s, nomor_tiket=%s, kelas_kabin=%s, pnr=%s
                            WHERE id=%s AND email_member=%s
                        """, [maskapai, asal, tujuan, tanggal, flight_number, nomor_tiket, kelas, pnr, klaim_id, email])
                    messages.success(request, 'Klaim berhasil diperbarui.')
                except Exception as e:
                    messages.error(request, f'Gagal memperbarui klaim: {str(e)}')
            else:
                messages.error(request, 'Klaim yang sudah Disetujui atau Ditolak tidak dapat diubah.')
        
        elif action == 'batalkan':
            status_klaim = request.POST.get('status_saat_ini')
            klaim_id = request.POST.get('klaim_id')
            if status_klaim == 'Menunggu':
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("DELETE FROM claim_missing_miles WHERE id=%s AND email_member=%s", [klaim_id, email])
                    messages.success(request, 'Klaim berhasil dibatalkan.')
                except Exception as e:
                    messages.error(request, f'Gagal membatalkan klaim: {str(e)}')
            else:
                messages.error(request, 'Klaim sudah diproses, tidak bisa dibatalkan.')
        
        return redirect('member:claim_list') 

    with connection.cursor() as cursor:
        query = """
            SELECT id, maskapai, bandara_asal AS asal, bandara_tujuan AS tujuan, bandara_asal || ' → ' || bandara_tujuan AS rute, 
                   tanggal_penerbangan AS tanggal_raw,
                   tanggal_penerbangan AS tanggal, flight_number AS flight, kelas_kabin AS kelas, nomor_tiket, pnr,
                   status_penerimaan AS status, timestamp
            FROM claim_missing_miles
            WHERE email_member = %s
        """
        params = [email]
        if filter_status != 'Semua':
            query += " AND status_penerimaan = %s"
            params.append(filter_status)
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, params)
        cols = [col[0] for col in cursor.description]
        klaim_list = [dict(zip(cols, row)) for row in cursor.fetchall()]
        
        cursor.execute("SELECT kode_maskapai, nama_maskapai FROM maskapai")
        maskapai_list = cursor.fetchall()
        
        cursor.execute("SELECT iata_code, nama, kota, negara FROM bandara")
        bandara_list = cursor.fetchall()

    return render(request, 'member/klaim.html', {
        'klaim_list': klaim_list,
        'filter_status': filter_status,
        'status_choices': ['Semua', 'Menunggu', 'Disetujui', 'Ditolak'],
        'maskapai_list': maskapai_list,
        'bandara_list': bandara_list,
    })

@login_required_member
def transfer_view(request):
    email = request.session.get('email')

    if request.method == 'POST':
        email_penerima = request.POST.get('email_penerima', '').strip()
        jumlah_raw = request.POST.get('jumlah', 0)
        catatan = request.POST.get('catatan', '')

        try:
            jumlah = int(jumlah_raw)
        except ValueError:
            messages.error(request, 'Jumlah miles harus berupa angka.')
            return redirect('member:transfer')

        if email_penerima == email:
            messages.error(request, 'Member tidak dapat mentransfer miles ke dirinya sendiri.')
        elif jumlah <= 0:
            messages.error(request, 'Jumlah miles harus lebih dari 0.')
        else:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT email FROM member WHERE email=%s", [email_penerima])
                    if not cursor.fetchone():
                        messages.error(request, 'Member penerima tidak ditemukan.')
                    else:
                        cursor.execute("SELECT total_miles FROM member WHERE email=%s", [email])
                        saldo = cursor.fetchone()[0]
                        if jumlah > saldo:
                            messages.error(request, f'Award miles tidak mencukupi. Saldo Anda: {saldo} miles.')
                        else:
                            cursor.execute("""
                                INSERT INTO transfer (email_member_1, email_member_2, jumlah, catatan)
                                VALUES (%s, %s, %s, %s)
                            """, [email, email_penerima, jumlah, catatan])
                            messages.success(request, f'Berhasil transfer {jumlah} miles ke {email_penerima}.')
            except Exception as e:
                messages.error(request, f'Gagal melakukan transfer: {str(e)}')
        
        return redirect('member:transfer')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.first_mid_name || ' ' || p.last_name AS nama_lengkap, m.email AS email_pengguna, m.total_miles AS award_miles
            FROM member m JOIN pengguna p ON m.email = p.email WHERE m.email = %s
        """, [email])
        member_data = dict(zip(['nama_lengkap', 'email_pengguna', 'award_miles'], cursor.fetchone()))

        cursor.execute("""
            SELECT timestamp, email_member_2 AS email, p.first_mid_name || ' ' || p.last_name AS member, -jumlah AS jumlah, catatan, 'Kirim' AS tipe
            FROM transfer t JOIN pengguna p ON t.email_member_2 = p.email WHERE t.email_member_1 = %s
            UNION ALL
            SELECT timestamp, email_member_1 AS email, p.first_mid_name || ' ' || p.last_name AS member, jumlah AS jumlah, catatan, 'Terima' AS tipe
            FROM transfer t JOIN pengguna p ON t.email_member_1 = p.email WHERE t.email_member_2 = %s
            ORDER BY timestamp DESC
        """, [email, email])
        cols = [col[0] for col in cursor.description]
        transfer_list = [dict(zip(cols, row)) for row in cursor.fetchall()]

    return render(request, 'member/transfer.html', {
        'member': member_data,
        'transfer_list': transfer_list,
        'email_session': email
    })

@login_required_member
def dashboard(request):
    email = request.session.get('email')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.first_mid_name || ' ' || p.last_name AS nama, 
                p.mobile_number AS telepon, 
                p.kewarganegaraan AS kewarganegaraan, 
                p.tanggal_lahir, 
                m.award_miles, m.total_miles, t.nama AS tier_nama
            FROM member m 
            JOIN pengguna p ON m.email = p.email 
            JOIN tier t ON m.id_tier = t.id_tier
            WHERE m.email = %s
        """, [email])
        row = cursor.fetchone()
        
        context = {
            'nama': row[0] if row else 'Nama Belum Diatur',
            'email': email,
            'telepon': row[1] if row else '-', 
            'kewarganegaraan': row[2] if row else 'Indonesia',
            'tanggal_lahir': row[3] if row else '-',
            'nomor_member': request.session.get('nomor_member', 'Belum Ada'),
            'tier': row[6] if row else 'BLUE',
            'total_miles': row[5] if row else 0,
            'award_miles': row[4] if row else 0,
        }

        cursor.execute("""
            SELECT tipe, timestamp, jumlah AS miles FROM (
                SELECT 'Transfer Keluar' AS tipe, timestamp, -jumlah AS jumlah FROM transfer WHERE email_member_1 = %s
                UNION ALL
                SELECT 'Transfer Masuk' AS tipe, timestamp, jumlah AS jumlah FROM transfer WHERE email_member_2 = %s
                UNION ALL
                SELECT 'Redeem' AS tipe, r.timestamp, -h.miles AS jumlah FROM redeem r JOIN hadiah h ON r.kode_hadiah = h.kode_hadiah WHERE r.email_member = %s
                UNION ALL
                SELECT 'Package' AS tipe, mp.timestamp, p.jumlah_award_miles AS jumlah FROM member_award_miles_package mp JOIN award_miles_package p ON mp.id_award_miles_package = p.id WHERE mp.email_member = %s
            ) t
            ORDER BY timestamp DESC LIMIT 5
        """, [email, email, email, email])
        cols = [col[0] for col in cursor.description]
        context['transaksi'] = [dict(zip(cols, row)) for row in cursor.fetchall()]

    return render(request, 'member/dashboard.html', context)



@login_required_member
def redeem_view(request):
    """
    Katalog hadiah + riwayat redeem milik member yang sedang login.

    Tabel:
        hadiah              (kode_hadiah, nama, miles, deskripsi, valid_start_date, program_end, id_penyedia)
        redeem              (email_member, kode_hadiah, timestamp)
        penyedia / mitra    (untuk nama penyedia)
    """
    email_member = request.session.get('email')
    active_tab = request.GET.get('tab', 'katalog')

    if request.method == 'POST':
        kode = request.POST.get('kode_hadiah', '').strip()

        try:
            with transaction.atomic():
                with connection.cursor() as cur:
                    # Ambil data hadiah
                    cur.execute("""
                        SELECT kode_hadiah, nama, miles
                        FROM hadiah
                        WHERE kode_hadiah = %s
                    """, [kode])

                    hadiah_row = cur.fetchone()

                    if not hadiah_row:
                        messages.error(request, 'Hadiah tidak ditemukan.')
                        return redirect('member:redeem')

                    kode_hadiah, nama_hadiah, miles_dibutuhkan = hadiah_row

                    cur.execute("""
                        SELECT award_miles
                        FROM member
                        WHERE email = %s
                        FOR UPDATE
                    """, [email_member])

                    member_row = cur.fetchone()

                    award_miles = member_row[0] if member_row else 0

                    if award_miles < miles_dibutuhkan:
                        messages.error(
                            request,
                            f'Award miles tidak mencukupi. '
                            f'Dibutuhkan {miles_dibutuhkan:,} miles, '
                            f'saldo Anda {award_miles:,} miles.'
                        )
                        return redirect('member:redeem')

                    now = timezone.now()

                    cur.execute("""
                        INSERT INTO redeem (
                            email_member,
                            kode_hadiah,
                            timestamp
                        )
                        VALUES (%s, %s, %s)
                    """, [email_member, kode_hadiah, now])

                    cur.execute("""
                        UPDATE member
                        SET award_miles = award_miles - %s
                        WHERE email = %s
                    """, [miles_dibutuhkan, email_member])

                    saldo_baru = award_miles - miles_dibutuhkan

            request.session['award_miles'] = saldo_baru

            messages.success(
                request,
                f'Berhasil redeem "{nama_hadiah}" '
                f'dengan {miles_dibutuhkan:,} miles.'
            )

        except Exception:
            messages.error(request, 'Terjadi kesalahan saat redeem hadiah.')

        return redirect('member:redeem')

    today = date.today()

    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                h.kode_hadiah,
                h.nama,
                h.miles,
                h.deskripsi,
                h.valid_start_date,
                h.program_end,
                COALESCE(m.nama_mitra, 'Mitra') AS nama_penyedia
            FROM hadiah h
            LEFT JOIN mitra m
                ON m.id_penyedia = h.id_penyedia
            WHERE h.program_end >= %s
            ORDER BY h.miles ASC
        """, [today])

        cols = [c.name for c in cur.description]

        hadiah_list = [
            dict(zip(cols, row))
            for row in cur.fetchall()
        ]

    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                r.timestamp,
                h.nama AS nama_hadiah,
                h.miles AS miles_digunakan,
                r.kode_hadiah
            FROM redeem r
            JOIN hadiah h
                ON h.kode_hadiah = r.kode_hadiah
            WHERE r.email_member = %s
            ORDER BY r.timestamp DESC
        """, [email_member])

        cols = [c.name for c in cur.description]

        riwayat_redeem = [
            dict(zip(cols, row))
            for row in cur.fetchall()
        ]

    with connection.cursor() as cur:
        cur.execute("""
            SELECT award_miles
            FROM member
            WHERE email = %s
        """, [email_member])

        row = cur.fetchone()
        award_miles = row[0] if row else 0

    request.session['award_miles'] = award_miles

    return render(request, 'member/redeem.html', {
        'hadiah_list': hadiah_list,
        'riwayat_redeem': riwayat_redeem,
        'active_tab': active_tab,
        'award_miles': award_miles,
    })


@login_required_member
def package_view(request):
    """
    Daftar paket award miles + riwayat pembelian member.

    Tabel:
        award_miles_package         (id, harga_paket, jumlah_award_miles)
        member_award_miles_package  (id_award_miles_package, email_member, timestamp)
    """
    email_member = request.session.get('email')

    if request.method == 'POST':
        pkg_id = request.POST.get('package_id', '').strip()

        try:
            with transaction.atomic():
                with connection.cursor() as cur:

                    cur.execute("""
                        SELECT
                            id,
                            harga_paket,
                            jumlah_award_miles
                        FROM award_miles_package
                        WHERE id = %s
                    """, [pkg_id])

                    row = cur.fetchone()

                    if not row:
                        messages.error(request, 'Paket tidak ditemukan.')
                        return redirect('member:package')

                    pkg_id_db, harga_paket, jumlah_award_miles = row

                    now = timezone.now()

                    cur.execute("""
                        INSERT INTO member_award_miles_package (
                            id_award_miles_package,
                            email_member,
                            timestamp
                        )
                        VALUES (%s, %s, %s)
                    """, [
                        pkg_id_db,
                        email_member,
                        now
                    ])

                    cur.execute("""
                        UPDATE member
                        SET award_miles = award_miles + %s
                        WHERE email = %s
                    """, [
                        jumlah_award_miles,
                        email_member
                    ])

                    # Ambil saldo terbaru
                    cur.execute("""
                        SELECT award_miles
                        FROM member
                        WHERE email = %s
                    """, [email_member])

                    saldo_baru = cur.fetchone()[0]

            request.session['award_miles'] = saldo_baru

            messages.success(
                request,
                f'Berhasil membeli '
                f'{jumlah_award_miles:,} Award Miles '
                f'seharga Rp {int(harga_paket):,}.'.replace(',', '.')
            )

        except Exception:
            messages.error(request, 'Terjadi kesalahan saat membeli package.')

        return redirect('member:package')

    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                id,
                harga_paket,
                jumlah_award_miles
            FROM award_miles_package
            ORDER BY jumlah_award_miles ASC
        """)

        cols = [c.name for c in cur.description]

        packages = [
            dict(zip(cols, row))
            for row in cur.fetchall()
        ]

    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                mp.timestamp,
                p.id AS package_id,
                p.jumlah_award_miles,
                p.harga_paket
            FROM member_award_miles_package mp
            JOIN award_miles_package p
                ON p.id = mp.id_award_miles_package
            WHERE mp.email_member = %s
            ORDER BY mp.timestamp DESC
        """, [email_member])

        cols = [c.name for c in cur.description]

        riwayat_package = [
            dict(zip(cols, row))
            for row in cur.fetchall()
        ]

    with connection.cursor() as cur:
        cur.execute("""
            SELECT award_miles
            FROM member
            WHERE email = %s
        """, [email_member])

        row = cur.fetchone()
        award_miles = row[0] if row else 0

    request.session['award_miles'] = award_miles

    return render(request, 'member/package.html', {
        'packages': packages,
        'riwayat_package': riwayat_package,
        'award_miles': award_miles,
    })


@login_required_member
def info_tier_view(request):
    """
    Tampilkan semua tier beserta keuntungan,
    posisi member saat ini,
    dan progress ke tier berikutnya.
    """

    email_member = request.session.get('email')

    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                id_tier,
                nama,
                minimal_frekuensi_terbang,
                minimal_tier_miles
            FROM tier
            ORDER BY minimal_tier_miles ASC
        """)

        rows = cur.fetchall()

        tiers = [
            {
                'id_tier': r[0],
                'nama': r[1],
                'minimal_frekuensi_terbang': r[2],
                'minimal_tier_miles': r[3],
                'keuntungan': keuntungan_tier(r[1]),
            }
            for r in rows
        ]

    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                id_tier,
                total_miles
            FROM member
            WHERE email = %s
        """, [email_member])

        row = cur.fetchone()

    current_id_tier = row[0] if row else 'T01'
    total_miles = row[1] if row else 0

    tier_ids = [t['id_tier'] for t in tiers]

    current_idx = (
        tier_ids.index(current_id_tier)
        if current_id_tier in tier_ids
        else 0
    )

    current_tier_obj = tiers[current_idx]

    next_tier = (
        tiers[current_idx + 1]
        if current_idx < len(tiers) - 1
        else None
    )

    progress_pct = 0

    if next_tier:
        curr_min = current_tier_obj['minimal_tier_miles']
        next_min = next_tier['minimal_tier_miles']

        if next_min > curr_min:
            progress_pct = max(
                0,
                min(
                    100,
                    int(
                        (total_miles - curr_min)
                        / (next_min - curr_min)
                        * 100
                    )
                )
            )

    return render(request, 'member/info_tier.html', {
        'tiers': tiers,
        'current_tier': current_tier_obj,
        'next_tier': next_tier,
        'total_miles': total_miles,
        'progress_pct': progress_pct,
    })


def keuntungan_tier(nama_tier: str) -> list[str]:
    """Mapping nama tier → list keuntungan (tidak ada tabel di DB)."""
    mapping = {
        'Blue'    : ['Akumulasi miles dasar', 'Akses penawaran khusus member'],
        'Silver'  : ['Bonus miles 25%', 'Priority check-in', 'Akses lounge partner'],
        'Gold'    : ['Bonus miles 50%', 'Priority boarding', 'Akses lounge premium', 'Extra bagasi 10kg'],
        'Platinum': ['Bonus miles 100%', 'Upgrade gratis', 'Akses lounge first class',
                     'Extra bagasi 20kg', 'Dedicated hotline'],
    }
    return mapping.get(nama_tier, [])
