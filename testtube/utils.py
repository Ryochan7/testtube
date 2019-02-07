import random, string

def randomword(length):
  letters = string.ascii_lowercase + string.ascii_uppercase
  return ''.join(random.choice(letters) for i in range(length))

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
