from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.humanize.templatetags.humanize import intcomma
from datetime import date

DUMMY_IDENTITAS = [
    {'nomor': 'A12345678', 'jenis': 'Paspor', 'negara': 'Indonesia',
     'tanggal_terbit': '2020-01-15', 'tanggal_habis': '2030-01-15', 'status': 'Aktif'},
    {'nomor': '327501234567890', 'jenis': 'KTP', 'negara': 'Indonesia',
     'tanggal_terbit': '2019-06-01', 'tanggal_habis': '2024-06-01', 'status': 'Kedaluwarsa'},
    {'nomor': 'SIM0001', 'jenis': 'SIM', 'negara': 'Indonesia',
     'tanggal_terbit': '2023-03-10', 'tanggal_habis': '2028-03-10', 'status': 'Aktif'},
]

DUMMY_MASKAPAI = [
    ('GA', 'GA - Garuda Indonesia'),
    ('QG', 'QG - Citilink'),
    ('JT', 'JT - Lion Air'),
    ('ID', 'ID - Batik Air'),
    ('SQ', 'SQ - Singapore Airlines'),
]

DUMMY_BANDARA = [
    ('CGK', 'CGK - Soekarno-Hatta, Jakarta'),
    ('DPS', 'DPS - Ngurah Rai, Bali'),
    ('SUB', 'SUB - Juanda, Surabaya'),
    ('SIN', 'SIN - Changi, Singapore'),
    ('NRT', 'NRT - Narita, Tokyo'),
    ('KUL', 'KUL - KLIA, Kuala Lumpur'),
    ('BKK', 'BKK - Suvarnabhumi, Bangkok'),
    ('HKG', 'HKG - Chek Lap Kok, Hong Kong'),
    ('SYD', 'SYD - Kingsford Smith, Sydney'),
    ('ICN', 'ICN - Incheon, Seoul'),
]

DUMMY_KLAIM = [
    {'id': 'CLM-001', 'maskapai': 'GA', 'rute': 'CGK → DPS',
     'tanggal': '2024-10-01', 'flight': 'GA404', 'kelas': 'Business',
     'status': 'Disetujui', 'timestamp': '2024-10-05 18:45:00'},
    {'id': 'CLM-002', 'maskapai': 'SQ', 'rute': 'SIN → NRT',
     'tanggal': '2024-11-15', 'flight': 'SQ12', 'kelas': 'Economy',
     'status': 'Menunggu', 'timestamp': '2024-11-20 18:45:00'},
    {'id': 'CLM-003', 'maskapai': 'GA', 'rute': 'CGK → SUB',
     'tanggal': '2025-01-10', 'flight': 'GA202', 'kelas': 'Economy',
     'status': 'Ditolak', 'timestamp': '2025-01-12 09:30:00'},
]

DUMMY_TRANSFER = [
    {'timestamp': '2025-01-15 10:30', 'member': 'Jane Smith',
     'email': 'jane@example.com', 'jumlah': -5000, 'catatan': 'Hadiah ulang tahun', 'tipe': 'Kirim'},
    {'timestamp': '2025-02-01 14:00', 'member': 'Budi A. Santoso',
     'email': 'budi@example.com', 'jumlah': 2000, 'catatan': '-', 'tipe': 'Terima'},
]

DUMMY_HADIAH = [
    {'kode': 'RWD-001', 'nama': 'Tiket Domestik PP', 'penyedia': 'Garuda Indonesia',
     'miles': 15000, 'deskripsi': 'Tiket pulang-pergi rute domestik Indonesia',
     'valid_start': '2024-01-01', 'program_end': '2025-12-31'},
    {'kode': 'RWD-002', 'nama': 'Upgrade Business Class', 'penyedia': 'Garuda Indonesia',
     'miles': 25000, 'deskripsi': 'Upgrade dari economy ke business class',
     'valid_start': '2026-01-01', 'program_end': '2027-01-01'},
    {'kode': 'RWD-003', 'nama': 'Voucher Hotel Rp500.000', 'penyedia': 'TravelokaPartner',
     'miles': 8000, 'deskripsi': 'Voucher hotel berlaku di seluruh Indonesia',
     'valid_start': '2024-06-01', 'program_end': '2025-06-30'},
    {'kode': 'RWD-004', 'nama': 'Akses Lounge 1x', 'penyedia': 'Plaza Premium',
     'miles': 3000, 'deskripsi': 'Akses lounge bandara premium 1 kali kunjungan',
     'valid_start': '2024-01-01', 'program_end': '2025-12-31'},
    {'kode': 'RWD-005', 'nama': 'Extra Bagasi 10kg', 'penyedia': 'Garuda Indonesia',
     'miles': 5000, 'deskripsi': 'Tambahan bagasi 10kg untuk 1 penerbangan',
     'valid_start': '2025-01-01', 'program_end': '2026-12-31'},
]

DUMMY_RIWAYAT_REDEEM = [
    {'hadiah': 'Akses Lounge 1x', 'timestamp': '2025-01-20 16:00', 'miles': -3000},
]

DUMMY_PACKAGES = [
    {'id': 'AMP-001', 'miles': 1000, 'harga': 'Rp 150.000'},
    {'id': 'AMP-002', 'miles': 5000, 'harga': 'Rp 650.000'},
    {'id': 'AMP-003', 'miles': 10000, 'harga': 'Rp 1.200.000'},
    {'id': 'AMP-004', 'miles': 25000, 'harga': 'Rp 2.750.000'},
    {'id': 'AMP-005', 'miles': 50000, 'harga': 'Rp 5.000.000'},
]

DUMMY_TIERS = [
    {'id': 'BLUE', 'nama': 'Blue', 'min_frekuensi': 0, 'min_miles': 0,
     'keuntungan': ['Akumulasi miles dasar', 'Akses penawaran khusus member']},
    {'id': 'SILVER', 'nama': 'Silver', 'min_frekuensi': 10, 'min_miles': 15000,
     'keuntungan': ['Bonus miles 25%', 'Priority check-in', 'Akses lounge partner']},
    {'id': 'GOLD', 'nama': 'Gold', 'min_frekuensi': 25, 'min_miles': 40000,
     'keuntungan': ['Bonus miles 50%', 'Priority boarding', 'Akses lounge premium', 'Extra bagasi 10kg']},
    {'id': 'PLATINUM', 'nama': 'Platinum', 'min_frekuensi': 50, 'min_miles': 80000,
     'keuntungan': ['Bonus miles 100%', 'Upgrade gratis', 'Akses lounge first class', 'Extra bagasi 20kg', 'Dedicated hotline']},
]

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
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'tambah':
            nomor = request.POST.get('nomor')

            sudah_ada = any(i['nomor'] == nomor for i in DUMMY_IDENTITAS)
            if sudah_ada:
                messages.error(request, 'Nomor dokumen sudah terdaftar.')
            else:
                DUMMY_IDENTITAS.append({
                    'nomor': nomor,
                    'jenis': request.POST.get('jenis'),
                    'negara': request.POST.get('negara'),
                    'tanggal_terbit': request.POST.get('tanggal_terbit'),
                    'tanggal_habis': request.POST.get('tanggal_habis'),
                    'status': 'Aktif',
                })
                messages.success(request, 'Identitas berhasil ditambahkan.')

        elif action == 'edit':
            nomor = request.POST.get('nomor')

            for identitas in DUMMY_IDENTITAS:
                if identitas['nomor'] == nomor:
                    identitas['jenis'] = request.POST.get('jenis')
                    identitas['negara'] = request.POST.get('negara')
                    identitas['tanggal_terbit'] = request.POST.get('tanggal_terbit')
                    identitas['tanggal_habis'] = request.POST.get('tanggal_habis')
                    identitas['status'] = request.POST.get('status', 'Aktif')
                    break

            messages.success(request, 'Identitas berhasil diperbarui.')

        elif action == 'hapus':
            nomor = request.POST.get('nomor')

            for identitas in DUMMY_IDENTITAS:
                if identitas['nomor'] == nomor:
                    DUMMY_IDENTITAS.remove(identitas)
                    break

            messages.success(request, 'Identitas berhasil dihapus.')

        return redirect('member:identitas')

    today = date.today()

    for identitas in DUMMY_IDENTITAS:
        tanggal_habis = date.fromisoformat(identitas['tanggal_habis'])

        if today > tanggal_habis:
            identitas['status'] = 'Kedaluwarsa'
        else:
            identitas['status'] = 'Aktif'

    return render(request, 'member/identitas.html', {
        'identitas_list': DUMMY_IDENTITAS,
    })

def claim_list(request):
    filter_status = request.GET.get('status', 'Semua')

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

            messages.success(request, f'Klaim untuk penerbangan {flight_number} ({asal} - {tujuan}) berhasil diajukan.')
            return redirect('member:claim_list')
        
        elif action == 'edit':
            status_klaim = request.POST.get('status_saat_ini') 
            if status_klaim == 'Menunggu':
                messages.success(request, 'Klaim berhasil diperbarui.')
            else:
                messages.error(request, 'Klaim yang sudah Disetujui atau Ditolak tidak dapat diubah.')
        
        elif action == 'batalkan':
            status_klaim = request.POST.get('status_saat_ini')
            if status_klaim == 'Menunggu':
                messages.success(request, 'Klaim berhasil dibatalkan.')
            else:
                messages.error(request, 'Klaim sudah diproses, tidak bisa dibatalkan.')
        
        return redirect('member:claim_list') 

    # R - Riwayat Klaim
    klaim_list_filtered = DUMMY_KLAIM
    if filter_status != 'Semua':
        klaim_list_filtered = [k for k in DUMMY_KLAIM if k['status'] == filter_status]

    return render(request, 'member/klaim.html', {
        'klaim_list': klaim_list_filtered,
        'filter_status': filter_status,
        'status_choices': ['Semua', 'Menunggu', 'Disetujui', 'Ditolak'],
    })

def transfer_view(request):
    member_dummy = {
        'nama_lengkap': 'Nisrina Alya',
        'email_pengguna': 'nisrina.alya@ui.ac.id',
        'award_miles': 32000
    }

    if request.method == 'POST':
        email_penerima = request.POST.get('email_penerima', '').strip()
        jumlah_raw = request.POST.get('jumlah', 0)
        catatan = request.POST.get('catatan', '')

        try:
            jumlah = int(jumlah_raw)
        except ValueError:
            messages.error(request, 'Jumlah miles harus berupa angka.')
            return redirect('member:transfer')

        if email_penerima == member_dummy['email_pengguna']:
            messages.error(request, 'Member tidak dapat mentransfer miles ke dirinya sendiri.')
        elif jumlah <= 0:
            messages.error(request, 'Jumlah miles harus lebih dari 0.')
        elif jumlah > member_dummy['award_miles']:
            messages.error(request, f'Award miles tidak mencukupi. Saldo Anda: {member_dummy["award_miles"]} miles.')
        else:
            messages.success(request, f'Berhasil transfer {jumlah} miles ke {email_penerima}.')
        
        return redirect('member:transfer')

    return render(request, 'member/transfer.html', {
        'member': member_dummy,
        'transfer_list': DUMMY_TRANSFER,
        'email_session': member_dummy['email_pengguna']
    })


login_required_member
def redeem_view(request):
    active_tab = request.GET.get('tab', 'katalog')

    if request.method == 'POST':
        kode = request.POST.get('kode_hadiah')
        hadiah = next((h for h in DUMMY_HADIAH if h['kode'] == kode), None)
        if hadiah:
            award_miles = request.session.get('award_miles', 0)
            if award_miles < hadiah['miles']:
                messages.error(request, f'Award miles tidak mencukupi. Dibutuhkan {hadiah["miles"]} miles.')
            else:
                messages.success(request, f'Berhasil redeem "{hadiah["nama"]}" dengan {hadiah["miles"]} miles.')
        return redirect('member:redeem')

    return render(request, 'member/redeem.html', {
        'hadiah_list': DUMMY_HADIAH,
        'riwayat_redeem': DUMMY_RIWAYAT_REDEEM,
        'active_tab': active_tab,
    })

@login_required_member
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

        # latest transaction (dummy) -> To Be Updated
        'transaksi': [
            {'tipe': 'Transfer', 'tanggal': '2026-04-26 10:31:20', 'miles': -1000},
            {'tipe': 'Redeem',   'tanggal': '2026-04-26 10:31:20', 'miles': -10000},
            {'tipe': 'Package',  'tanggal': '2026-04-26 10:31:20', 'miles': +16000},
            {'tipe': 'Package',  'tanggal': '2026-04-26 10:31:20', 'miles': +16000},
            {'tipe': 'Redeem',   'tanggal': '2026-04-26 10:31:20', 'miles': -10000},
        ],
    }
    return render(request, 'member/dashboard.html', context)

def package_view(request):
    if request.method == 'POST':
        pkg_id = request.POST.get('package_id')
        pkg = next((p for p in DUMMY_PACKAGES if p['id'] == pkg_id), None)
        if pkg:
            messages.success(request, f'Berhasil membeli {pkg["miles"]:,} Award Miles dengan harga {pkg["harga"]}.')
        return redirect('member:package')

    return render(request, 'member/package.html', {
        'packages': DUMMY_PACKAGES,
    })


def info_tier_view(request):
    current_tier = request.session.get('tier', 'Blue')
    total_miles = request.session.get('total_miles', 0)

    tier_names = [t['nama'] for t in DUMMY_TIERS]
    current_idx = tier_names.index(current_tier) if current_tier in tier_names else 0
    next_tier = DUMMY_TIERS[current_idx + 1] if current_idx < len(DUMMY_TIERS) - 1 else None

    progress_pct = 0
    if next_tier:
        curr_min = DUMMY_TIERS[current_idx]['min_miles']
        next_min = next_tier['min_miles']
        if next_min > curr_min:
            progress_pct = min(100, int((total_miles - curr_min) / (next_min - curr_min) * 100))

    return render(request, 'member/info_tier.html', {
        'tiers': DUMMY_TIERS,
        'current_tier': current_tier,
        'next_tier': next_tier,
        'total_miles': total_miles,
        'progress_pct': progress_pct,
    })