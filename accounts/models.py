from django.db import models

class Pengguna(models.Model):
    email = models.EmailField(max_length=100, primary_key=True)
    password = models.CharField(max_length=255)
    salutation = models.CharField(max_length=10)
    first_mid_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    country_code = models.CharField(max_length=5)
    mobile_number = models.CharField(max_length=20)
    tanggal_lahir = models.DateField()
    kewarganegaraan = models.CharField(max_length=50)

    class Meta:
        db_table = 'pengguna'
        managed = False


class Tier(models.Model):
    id_tier = models.CharField(max_length=10, primary_key=True)
    nama = models.CharField(max_length=50)
    minimal_frekuensi_terbang = models.IntegerField()
    minimal_tier_miles = models.IntegerField()

    class Meta:
        db_table = 'tier'
        managed = False


class Maskapai(models.Model):
    kode_maskapai = models.CharField(max_length=10, primary_key=True)
    nama_maskapai = models.CharField(max_length=100)

    class Meta:
        db_table = 'maskapai'
        managed = False


class Member(models.Model):
    email = models.OneToOneField(
        Pengguna,
        on_delete=models.CASCADE,
        db_column='email',
        primary_key=True
    )
    nomor_member = models.CharField(max_length=20, unique=True)
    tanggal_bergabung = models.DateField()
    id_tier = models.ForeignKey(
        Tier,
        on_delete=models.PROTECT,
        db_column='id_tier'
    )
    award_miles = models.IntegerField(null=True, blank=True)
    total_miles = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'member'
        managed = False


class Staf(models.Model):
    email = models.OneToOneField(
        Pengguna,
        on_delete=models.CASCADE,
        db_column='email',
        primary_key=True
    )
    id_staf = models.CharField(max_length=20, unique=True)
    kode_maskapai = models.ForeignKey(
        Maskapai,
        on_delete=models.PROTECT,
        db_column='kode_maskapai'
    )

    class Meta:
        db_table = 'staf'
        managed = False