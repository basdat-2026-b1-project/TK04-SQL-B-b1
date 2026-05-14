from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.contrib.auth.hashers import check_password, make_password
from .models import Pengguna, Member, Staf
from datetime import date


def landing_page(request):
    return render(request, 'base.html')


def login_view(request):
    if request.session.get('role'):
        if request.session.get('role') == 'member':
            return redirect('/member/dashboard/')
        elif request.session.get('role') == 'staf':
            return redirect('/staff/dashboard/')

    if request.method == 'POST':
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        # Ambil data pengguna dari DB
        with connection.cursor() as cur:
            cur.execute("""
                SELECT email, password, salutation, first_mid_name, last_name,
                       country_code, mobile_number, tanggal_lahir, kewarganegaraan
                FROM pengguna
                WHERE email = %s
            """, [email])
            row = cur.fetchone()

        if not row:
            messages.error(request, 'Email atau password salah. Silakan coba lagi.')
            return render(request, 'accounts/login.html')

        (db_email, db_password, salutation, first_mid_name, last_name,
         country_code, mobile_number, tanggal_lahir, kewarganegaraan) = row

        # Cek password (support hashed maupun plaintext sementara)
        password_valid = check_password(password, db_password)

        if not password_valid:
            messages.error(request, 'Email atau password salah. Silakan coba lagi.')
            return render(request, 'accounts/login.html')

        # Set session dasar
        request.session['email']          = db_email
        request.session['salutation']     = salutation
        request.session['first_mid_name'] = first_mid_name
        request.session['last_name']      = last_name
        request.session['nama']           = f"{first_mid_name} {last_name}"
        request.session['country_code']   = country_code
        request.session['mobile_number']  = mobile_number
        request.session['tanggal_lahir']  = str(tanggal_lahir)
        request.session['kewarganegaraan']= kewarganegaraan

        # Cek apakah member
        with connection.cursor() as cur:
            cur.execute("""
                SELECT m.nomor_member, m.tanggal_bergabung, m.id_tier,
                       m.award_miles, m.total_miles, t.nama
                FROM member m
                JOIN tier t ON t.id_tier = m.id_tier
                WHERE m.email = %s
            """, [email])
            member_row = cur.fetchone()

        if member_row:
            request.session['role']              = 'member'
            request.session['nomor_member']      = member_row[0]
            request.session['tanggal_bergabung'] = str(member_row[1])
            request.session['id_tier']           = member_row[2]
            request.session['award_miles']       = member_row[3]
            request.session['total_miles']       = member_row[4]
            request.session['tier']              = member_row[5]

            messages.success(request, f"Selamat datang, {salutation} {first_mid_name} {last_name}!")
            return redirect('/member/dashboard/')

        # Cek apakah staf
        with connection.cursor() as cur:
            cur.execute("""
                SELECT s.id_staf, s.kode_maskapai, mk.nama_maskapai
                FROM staf s
                JOIN maskapai mk ON mk.kode_maskapai = s.kode_maskapai
                WHERE s.email = %s
            """, [email])
            staf_row = cur.fetchone()

        if staf_row:
            request.session['role']          = 'staf'
            request.session['id_staf']       = staf_row[0]
            request.session['kode_maskapai'] = staf_row[1]
            request.session['maskapai']      = staf_row[2]

            messages.success(request, f"Selamat datang, {salutation} {first_mid_name} {last_name}!")
            return redirect('/staff/dashboard/')

        # Email ada di pengguna tapi bukan member/staf
        messages.error(request, 'Akun tidak memiliki role yang valid.')

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
        role       = request.POST.get('role', 'member')
        email      = request.POST.get('email', '').strip()
        password   = request.POST.get('password', '')

        if not email:
            messages.error(request, 'Email tidak boleh kosong.')
            return render(request, 'accounts/register.html', {'maskapai_choices': MASKAPAI_CHOICES})

        # Cek apakah email sudah ada
        with connection.cursor() as cur:
            cur.execute("SELECT email FROM pengguna WHERE email = %s", [email])
            if cur.fetchone():
                messages.error(request, 'Email sudah terdaftar.')
                return render(request, 'accounts/register.html', {'maskapai_choices': MASKAPAI_CHOICES})

        hashed_password = make_password(password)
        salutation      = request.POST.get('salutation', '')
        first_mid_name  = request.POST.get('first_mid_name', '')
        last_name       = request.POST.get('last_name', '')
        country_code    = request.POST.get('country_code')
        mobile_number   = request.POST.get('mobile_number')
        tanggal_lahir   = request.POST.get('tanggal_lahir')
        kewarganegaraan = request.POST.get('kewarganegaraan')
        tanggal_lahir   = request.POST.get('tanggal_lahir')
        if not tanggal_lahir:
            tanggal_lahir = None

        with connection.cursor() as cur:
            # Insert ke pengguna
            cur.execute("""
                INSERT INTO pengguna (
                    email, password, salutation, first_mid_name, last_name,
                    country_code, mobile_number, tanggal_lahir, kewarganegaraan
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [email, hashed_password, salutation, first_mid_name, last_name,
                  country_code, mobile_number, tanggal_lahir, kewarganegaraan])

            if role == 'member':
                # Generate nomor member
                cur.execute("SELECT COUNT(*) FROM member")
                count        = cur.fetchone()[0]
                nomor_member = f"M{count + 1:04d}"

                cur.execute("""
                    INSERT INTO member (email, nomor_member, tanggal_bergabung, id_tier, award_miles, total_miles)
                    VALUES (%s, %s, %s, 'T01', 0, 0)
                """, [email, nomor_member, date.today()])

            elif role == 'staf':
                kode_maskapai = request.POST.get('kode_maskapai', '')
                cur.execute("SELECT COUNT(*) FROM staf")
                count   = cur.fetchone()[0]
                id_staf = f"S{count + 1:04d}"

                cur.execute("""
                    INSERT INTO staf (email, id_staf, kode_maskapai)
                    VALUES (%s, %s, %s)
                """, [email, id_staf, kode_maskapai])

        messages.success(request, 'Akun berhasil dibuat! Silakan login.')
        return redirect('accounts:login')
    return render(request, 'accounts/register.html', {'maskapai_choices': MASKAPAI_CHOICES})

def logout_view(request):
    request.session.flush()
    messages.success(request, 'Anda telah berhasil logout.')
    return redirect('accounts:login')

def dashboard_view(request):
    if not request.session.get('role'):
        return redirect('accounts:login')

    role = request.session.get('role')

    if role == 'member':
        return redirect('/member/dashboard/')
    elif role == 'staf':
        return redirect('/staff/dashboard/')

    return redirect('accounts:login')


def profile_view(request):
    if not request.session.get('role'):
        return redirect('accounts:login')

    role = request.session.get('role')

    context = {
        'email'          : request.session.get('email', ''),
        'role'           : role,
        'salutation'     : request.session.get('salutation', ''),
        'first_mid_name' : request.session.get('first_mid_name', ''),
        'last_name'      : request.session.get('last_name', ''),
        'country_code'   : request.session.get('country_code', ''),
        'mobile_number'  : request.session.get('mobile_number', ''),
        'tanggal_lahir'  : request.session.get('tanggal_lahir', ''),
        'kewarganegaraan': request.session.get('kewarganegaraan', ''),
        'nomor_member'   : request.session.get('nomor_member', ''),
        'tanggal_bergabung': request.session.get('tanggal_bergabung', ''),
        'id_staf'        : request.session.get('id_staf', ''),
        'kode_maskapai'  : request.session.get('kode_maskapai', ''),
        'maskapai_choices': [
            ('GA', 'Garuda Indonesia'),
            ('QG', 'Citilink'),
            ('JT', 'Lion Air'),
            ('ID', 'Batik Air'),
            ('SQ', 'Singapore Airlines'),
        ],
    }

    if role == 'member':
        return render(request, 'profile_member.html', context)
    elif role == 'staf':
        return render(request, 'profile_staff.html', context)

    return redirect('accounts:dashboard')


def update_profile(request):
    if not request.session.get('role'):
        return redirect('accounts:login')

    if request.method == 'POST':
        email           = request.session.get('email')
        salutation      = request.POST.get('salutation', '')
        first_mid_name  = request.POST.get('first_mid_name', '')
        last_name       = request.POST.get('last_name', '')
        kewarganegaraan = request.POST.get('kewarganegaraan', '')
        country_code    = request.POST.get('country_code', '')
        mobile_number   = request.POST.get('mobile_number', '')
        tanggal_lahir   = request.POST.get('tanggal_lahir', '')

        with connection.cursor() as cur:
            cur.execute("""
                UPDATE pengguna
                SET salutation = %s, first_mid_name = %s, last_name = %s,
                    kewarganegaraan = %s, country_code = %s,
                    mobile_number = %s, tanggal_lahir = %s
                WHERE email = %s
            """, [salutation, first_mid_name, last_name, kewarganegaraan,
                  country_code, mobile_number, tanggal_lahir, email])

            if request.session.get('role') == 'staf':
                kode_maskapai = request.POST.get('kode_maskapai', '')
                cur.execute(
                    "UPDATE staf SET kode_maskapai = %s WHERE email = %s",
                    [kode_maskapai, email]
                )
                request.session['kode_maskapai'] = kode_maskapai

        # Sync session
        request.session['salutation']      = salutation
        request.session['first_mid_name']  = first_mid_name
        request.session['last_name']       = last_name
        request.session['nama']            = f"{first_mid_name} {last_name}"
        request.session['kewarganegaraan'] = kewarganegaraan
        request.session['country_code']    = country_code
        request.session['mobile_number']   = mobile_number
        request.session['tanggal_lahir']   = tanggal_lahir

        messages.success(request, 'Profil berhasil diperbarui.')

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

    email             = request.session.get('email')
    password_lama     = request.POST.get('password_lama', '')
    password_baru     = request.POST.get('password_baru', '')
    konfirmasi_password = request.POST.get('konfirmasi_password_baru', '')

    with connection.cursor() as cur:
        cur.execute("SELECT password FROM pengguna WHERE email = %s", [email])
        row = cur.fetchone()

    if not row:
        messages.error(request, 'Data pengguna tidak ditemukan.')
        return redirect('accounts:profile')

    if not check_password(password_lama, row[0]):
        messages.error(request, 'Password lama tidak sesuai.')
    elif password_baru != konfirmasi_password:
        messages.error(request, 'Konfirmasi password baru tidak cocok.')
    elif len(password_baru) < 8:
        messages.error(request, 'Password baru minimal 8 karakter.')
    else:
        hashed = make_password(password_baru)
        with connection.cursor() as cur:
            cur.execute(
                "UPDATE pengguna SET password = %s WHERE email = %s",
                [hashed, email]
            )
        messages.success(request, 'Password berhasil diubah.')

    return redirect('accounts:profile')