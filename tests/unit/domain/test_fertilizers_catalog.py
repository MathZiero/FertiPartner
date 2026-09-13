"""Testes unitários rigorosos para o catálogo de domínio de fertilizantes."""

import re
import pytest
from domain.fertilizers import FERTILIZERS_CATALOG


class TestFertilizersCatalogDomain:
    """Validações estritas de integridade do catálogo de fertilizantes NPK."""

    REQUIRED_FIELDS = {
        "id",
        "slug",
        "canonical_name",
        "category_name",
        "chemical_formula",
        "cas_rn",
        "description",
        "detailed_description",
        "agronomic_usage",
        "physical_properties",
        "handling_storage",
        "typical_nutrients",
        "synonyms",
        "hs_ncm_codes",
    }

    EXPECTED_SLUGS = {
        "ureia",
        "map",
        "dap",
        "cloreto-de-potassio",
        "amonia-anidra",
        "nitrato-de-amonio",
        "sulfato-de-amonio",
        "ssp",
        "tsp",
        "rocha-fosfatica",
        "sulfato-de-potassio",
        "enxofre-elementar",
    }

    def test_catalog_size_and_slugs(self):
        assert len(FERTILIZERS_CATALOG) == 12, "O catálogo canônico deve conter exatamente 12 produtos homologados."
        actual_slugs = {f["slug"] for f in FERTILIZERS_CATALOG}
        assert actual_slugs == self.EXPECTED_SLUGS

    def test_catalog_unique_and_valid_ids(self):
        ids = [f["id"] for f in FERTILIZERS_CATALOG]
        assert len(ids) == len(set(ids)), "IDs de fertilizantes devem ser estritamente únicos."
        for item_id in ids:
            assert isinstance(item_id, int)
            assert 1 <= item_id <= 12

    def test_required_fields_present_and_non_empty(self):
        for fert in FERTILIZERS_CATALOG:
            slug = fert.get("slug", "unknown")
            for field_name in self.REQUIRED_FIELDS:
                assert field_name in fert, f"Campo obrigatório '{field_name}' ausente em '{slug}'."
                val = fert[field_name]
                if isinstance(val, (str, list, dict)):
                    assert len(val) > 0, f"Campo '{field_name}' não pode ser vazio em '{slug}'."

    def test_chemical_formula_and_cas_format(self):
        # CAS Registry Number format: digits-digits-digit
        cas_pattern = re.compile(r"^\d{2,7}-\d{2}-\d$")
        for fert in FERTILIZERS_CATALOG:
            cas = fert["cas_rn"]
            formula = fert["chemical_formula"]
            assert len(formula.strip()) > 0
            assert cas_pattern.match(cas), f"CAS RN '{cas}' inválido para {fert['slug']}."

    def test_typical_nutrients_percentages(self):
        for fert in FERTILIZERS_CATALOG:
            nutrients = fert["typical_nutrients"]
            assert isinstance(nutrients, dict)
            for nutrient_label, percentage in nutrients.items():
                assert isinstance(percentage, (int, float)), f"Teor de {nutrient_label} deve ser numérico em {fert['slug']}."
                assert 0.0 < percentage <= 100.0, f"Teor {percentage}% de {nutrient_label} fora dos limites agronômicos (0..100) em {fert['slug']}."

    def test_hs_ncm_codes_validity(self):
        for fert in FERTILIZERS_CATALOG:
            codes = fert["hs_ncm_codes"]
            assert isinstance(codes, list)
            assert len(codes) >= 1
            for code in codes:
                assert isinstance(code, str)
                assert code.isdigit(), f"Código NCM/HS '{code}' deve ser composto apenas por dígitos numéricos em {fert['slug']}."
                assert len(code) in (6, 8), f"Código NCM/HS '{code}' deve possuir 6 (HS) ou 8 (NCM) dígitos em {fert['slug']}."
