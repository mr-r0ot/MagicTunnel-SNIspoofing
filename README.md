# MagicTunnel-SNIspoofing
Sweet tool to find and use unfiltered domains behind Cloudflare and forge requests to Cloudflare and as a result, configs made with Cloudflare worker methods will work. - ابزار شیرین برای پیدا کردن و استفاده از دامنه های فیلتر نشده پشت کلود فلر و جعل درخواست ها به کلود فلر و در نتیجه به کار افتادن کانفیگ های ساخته شده با روش های کلودفلر ورکر.


# دقیقا چیست؟
این ابزار یک اسکنر دامنه های پر استفاده پشت کلودفلر هست و هسته SNI SPOOF استفاده می کند

# استفاده
```
python MagicTunnel.py

# or

sudo python MagicTunnel.py
```


# تبدیل کانفیگ های بر پیاه کلود فلر ورکر cfw به قابل استفاده با هسته SNI SPOOF (تغییر IP و PORT)
```
python VlessGrow.py
```

# تمام هسته متلق می باشد به سازنده اصلی
https://github.com/patterniha/SNI-Spoofing
