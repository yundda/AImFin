# analysis/schemas/recommend_response.py
RECOMMEND_RESPONSE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "allocations": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "bucket": {
                        "type": "string",
                        "enum": [
                            "STOCKS_KR", "STOCKS_GLB",
                            "BONDS_KR", "BONDS_GLB",
                            "ALTERNATIVES", "FUNDS", "CASH"
                        ]
                    },
                    "weight_pct": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "assets": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "code": {"type": "string"},
                                "weight_pct": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 100
                                }
                            },
                            "required": ["code", "weight_pct"]
                        },
                        "default": []
                    }
                },
                # ★ GMS 요구: properties에 있는 키는 모두 required에 포함 (assets 포함)
                "required": ["bucket", "weight_pct", "assets"]
            }
        },
        "rationale": {"type": "string"},
        "summary":   {"type": "string"},
        "risks":     {"type": "string"}
    },
    # ★ 최상위도 모든 키를 required에 포함
    "required": ["allocations", "rationale", "summary", "risks"]
}