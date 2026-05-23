from src.lgpd.anonymizer import Anonymizer


class TestAnonymizer:
    def setup_method(self):
        self.anonymizer = Anonymizer()

    def test_mask_cpf_valid(self):
        result = self.anonymizer.mask_cpf("123.456.789-00")
        assert result == "***.456.***-**"

    def test_mask_cpf_invalid(self):
        result = self.anonymizer.mask_cpf("123")
        assert result == "***.***.***-**"

    def test_hash_value_deterministic(self):
        h1 = self.anonymizer.hash_value("Maria Silva")
        h2 = self.anonymizer.hash_value("Maria Silva")
        assert h1 == h2

    def test_hash_value_different_inputs(self):
        h1 = self.anonymizer.hash_value("Maria Silva")
        h2 = self.anonymizer.hash_value("Joao Santos")
        assert h1 != h2

    def test_anonymize_record(self):
        record = {
            "cpf": "123.456.789-00",
            "nome": "Maria Silva",
            "endereco": "Rua A, 123",
        }
        result = self.anonymizer.anonymize_record(record)
        assert result["cpf"] == "***.456.***-**"
        assert result["nome"] != "Maria Silva"
        assert result["endereco"] != "Rua A, 123"
        assert len(result["nome"]) == 16
        assert len(result["endereco"]) == 16

    def test_anonymize_batch(self):
        records = [
            {"cpf": "111.222.333-44", "nome": "A"},
            {"cpf": "555.666.777-88", "nome": "B"},
        ]
        results = self.anonymizer.anonymize_batch(records)
        assert len(results) == 2
        assert results[0]["cpf"] == "***.222.***-**"
        assert results[1]["cpf"] == "***.666.***-**"
