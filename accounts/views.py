from urllib import request

from django.shortcuts import render, redirect
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib.auth.hashers import check_password, make_password
from .models import Pengguna, Member, Staf, Maskapai
from datetime import date

DUMMY_USERS = {
    'john@example.com': {
        'password': 'password123',
        'role': 'member',
        'salutation': 'Mr.',
        'nama': 'John William Doe',
        'first_mid_name': 'John William',
        'last_name': 'Doe',
        'country_code': '+62',
        'mobile_number': '81234567890',
        'tanggal_lahir': '1990-05-15',
        'kewarganegaraan': 'Indonesia',
        'nomor_member': 'M0001',
        'tanggal_bergabung': '2024-01-15',
        'tier': 'Gold',
        'total_miles': 45000,
        'award_miles': 32000,
    },
    'admin@aeromiles.com': {
        'password': 'admin123',
        'role': 'staf',
        'salutation': 'Mr.',
        'nama': 'Admin Aero',
        'first_mid_name': 'Admin',
        'last_name': 'Aero',
        'country_code': '+62',
        'mobile_number': '81111111111',
        'tanggal_lahir': '1988-01-01',
        'kewarganegaraan': 'Indonesia',
        'id_staf': 'S0001',
        'maskapai': 'Garuda Indonesia',
        'kode_maskapai': 'GA',
    },
}

DUMMY_TRANSAKSI_TERBARU = [
    {'tipe': 'Transfer', 'timestamp': '2025-01-15 10:30', 'jumlah': -5000},
    {'tipe': 'Redeem', 'timestamp': '2025-01-20 16:00', 'jumlah': -3000},
    {'tipe': 'Package', 'timestamp': '2025-03-01 08:00', 'jumlah': 10000},
    {'tipe': 'Klaim', 'timestamp': '2024-10-05 18:45', 'jumlah': 2500},
    {'tipe': 'Transfer', 'timestamp': '2024-12-10 14:00', 'jumlah': 2000},
]

def landing_page(request):
    return render(request, 'base.html')

def login_view(request):
    # cek jika user sudah login sebelumnya
    if request.session.get('role'):
        if request.session.get('role') == 'member':
            return redirect('/member/dashboard/') # sesuaikan dengan nama path urls.py per role, misal: redirect('member:dashboard')
        elif request.session.get('role') == 'staf':
            return redirect('/staff/dashboard/')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        user = DUMMY_USERS.get(email)
        if user and user['password'] == password:

            request.session['email'] = email
            request.session['role'] = user['role']
            request.session['salutation'] = user['salutation']
            request.session['nama'] = user['nama']

            for k, v in user.items():
                if k != 'password':
                    request.session[k] = v
            messages.success(request, f"Selamat datang, {user['salutation']} {user['nama']}!")
            
            # 2. Ubah bagian redirect setelah POST login berhasil
            if user['role'] == 'member':
                return redirect('/member/dashboard/') 
            elif user['role'] == 'staf':
                return redirect('/staff/dashboard/')
        else:
            messages.error(request, 'Email atau password salah. Silakan coba lagi.')

    return render(request, 'accounts/login.html')


def register_view(request):
    if request.session.get('role'):
        return redirect('accounts:dashboard')

    MASKAPAI_CHOICES = [
        ('GA', 'GA - Garuda Indonesia'),
        ('QG', 'QG - Citilink'),
        ('JT', 'JT - Lion Air'),
        ('ID', 'ID - Batik Air'),
        ('SQ', 'SQ - Singapore Airlines'),
    ]

    if request.method == 'POST':
        role = request.POST.get('role', 'member')
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        tanggal_bergabung = date.today()
        
        # validate
        if not email:
            messages.error(request, 'Email tidak boleh kosong.')
        elif email in DUMMY_USERS:
            messages.error(request, 'Email sudah terdaftar.')
        else:
            # simpan data dummy baru ke dalam dictionary, data selain dummy data
            DUMMY_USERS[email] = {
                'password': password,
                'role': role,
                'salutation': request.POST.get('salutation', ''),
                'nama': request.POST.get('nama_depan', '') + ' ' + request.POST.get('nama_belakang', ''),
            }
            messages.success(request, 'Akun berhasil dibuat! Silakan login.')
            return redirect('accounts:login')

    # dijalankan saat halaman pertama kali dibuka (GET request)
    return render(request, 'accounts/register.html', {'maskapai_choices': MASKAPAI_CHOICES})


def logout_view(request):
    request.session.flush()
    messages.info(request, 'Anda telah logout.')
    return redirect('accounts:login')


def dashboard_view(request):
    if not request.session.get('role'):
        return redirect('accounts:login')

    role = request.session.get('role')

    if role == 'member':
        context = {
            'transaksi_terbaru': DUMMY_TRANSAKSI_TERBARU,
        }
    else:  # staf
        context = {
            'klaim_menunggu': 7,
            'klaim_disetujui': 12,
            'klaim_ditolak': 3,
        }
    return render(request, 'dashboard.html', context)


def profile_view(request):
    if not request.session.get('role'):
        return redirect('accounts:login')

    role = request.session.get('role')

    context = {
        'email': request.session.get('email', ''),
        'role': role,
        'salutation': request.session.get('salutation', ''),
        'first_mid_name': request.session.get('first_mid_name', ''),
        'last_name': request.session.get('last_name', ''),
        'country_code': request.session.get('country_code', ''),
        'mobile_number': request.session.get('mobile_number', ''),
        'tanggal_lahir': request.session.get('tanggal_lahir', ''),
        'kewarganegaraan': request.session.get('kewarganegaraan', ''),
        'nomor_member': request.session.get('nomor_member', ''),
        'tanggal_bergabung': request.session.get('tanggal_bergabung', ''),
        'id_staf': request.session.get('id_staf', ''),
        'kode_maskapai': request.session.get('kode_maskapai', ''),
        'maskapai_choices': [
            ('GA', 'Garuda Indonesia'),
            ('QG', 'Citilink'),
            ('JT', 'Lion Air'),
            ('ID', 'Batik Air'),
            ('SQ', 'Singapore Airlines'),
        ],
    }

    if request.session.get('role') == 'member':
        context['nomor_member'] = request.session.get('nomor_member', '')
        context['tanggal_bergabung'] = request.session.get('tanggal_bergabung', '')
        return render(request, 'profile_member.html', context)

    if role == 'staf':
        context['id_staf'] = request.session.get('id_staf', '')
        context['kode_maskapai'] = request.session.get('kode_maskapai', '')
        return render(request, 'profile_staff.html', context)

    return redirect('accounts:dashboard')

def update_profile(request):
    if not request.session.get('role'):
        return redirect('accounts:login')

    if request.method == 'POST':
        request.session['salutation'] = request.POST.get('salutation', '')
        request.session['first_mid_name'] = request.POST.get('first_mid_name', '')
        request.session['last_name'] = request.POST.get('last_name', '')
        request.session['kewarganegaraan'] = request.POST.get('kewarganegaraan', '')
        request.session['country_code'] = request.POST.get('country_code', '')
        request.session['mobile_number'] = request.POST.get('mobile_number', '')
        request.session['tanggal_lahir'] = request.POST.get('tanggal_lahir', '')

        if request.session.get('role') == 'staf':
            request.session['kode_maskapai'] = request.POST.get('kode_maskapai', '')

        request.session['nama'] = (
            request.session['first_mid_name'] + ' ' + request.session['last_name']
        )

    return redirect('accounts:profile')

def update_profile_photo(request):
    if not request.session.get('role'):
        return redirect('accounts:login')

    if request.method == 'POST':
        messages.info(request, 'Upload foto belum disambungkan ke database/media.')

    return redirect('accounts:profile')


def update_password(request):
    if not request.session.get('email'):
        return redirect('accounts:login')

    if request.method != 'POST':
        return redirect('accounts:profile')

    email = request.session.get('email')
    password_lama = request.POST.get('password_lama', '')
    password_baru = request.POST.get('password_baru', '')
    konfirmasi_password = request.POST.get('konfirmasi_password_baru', '')

    try:
        pengguna = Pengguna.objects.get(email=email)
    except Pengguna.DoesNotExist:
        messages.error(request, 'Data pengguna tidak ditemukan.')
        return redirect('accounts:profile')

    if not check_password(password_lama, pengguna.password):
        messages.error(request, 'Password lama tidak sesuai.')
    elif password_baru != konfirmasi_password:
        messages.error(request, 'Konfirmasi password baru tidak cocok.')
    elif len(password_baru) < 8:
        messages.error(request, 'Password baru minimal 8 karakter.')
    else:
        pengguna.password = make_password(password_baru)
        pengguna.save()
        messages.success(request, 'Password berhasil diubah.')

    return redirect('accounts:profile')