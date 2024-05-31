import uuid
import base64

def generate_unique_code():
    # Создаем UUID4
    uuid_bytes = uuid.uuid4().bytes
    # Кодируем в base64 и удаляем ненужные символы
    code = base64.urlsafe_b64encode(uuid_bytes).rstrip(b'=').decode('ascii')
    return code[:12]  # Обрезаем до нужной длины

# Пример использования
print(generate_unique_code())