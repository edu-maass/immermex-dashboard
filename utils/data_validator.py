"""
Validador avanzado de datos para procesamiento de Excel
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    cleaned_data: Optional[pd.DataFrame] = None
    validation_stats: Optional[Dict[str, Any]] = None

@dataclass
class ColumnValidationRule:
    column_name: str
    required: bool = True
    data_type: Optional[type] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None
    custom_validator: Optional[callable] = None

class AdvancedDataValidator:
    """Validador avanzado de datos para archivos Excel"""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.MODERATE):
        self.validation_level = validation_level
        self.validation_rules: Dict[str, List[ColumnValidationRule]] = {}
        self.setup_default_rules()
    
    def setup_default_rules(self):
        """Configura reglas de validación por defecto para cada tipo de datos"""
        
        # Reglas para facturación
        self.validation_rules['facturacion'] = [
            ColumnValidationRule('fecha_factura', required=True, data_type=datetime),
            ColumnValidationRule('serie_factura', required=True, min_length=1, max_length=20),
            ColumnValidationRule('folio_factura', required=True, data_type=int),
            ColumnValidationRule('cliente', required=True, min_length=1, max_length=255),
            ColumnValidationRule('monto_total', required=True, data_type=float, min_value=0),
            ColumnValidationRule('monto_neto', required=False, data_type=float, min_value=0),
            ColumnValidationRule('saldo_pendiente', required=False, data_type=float, min_value=0),
            ColumnValidationRule('dias_credito', required=False, data_type=int, min_value=0, max_value=365),
            ColumnValidationRule('agente', required=False, max_length=100),
            ColumnValidationRule('uuid_factura', required=False, pattern=r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
        ]
        
        # Reglas para cobranza
        self.validation_rules['cobranza'] = [
            ColumnValidationRule('fecha_pago', required=True, data_type=datetime),
            ColumnValidationRule('serie_pago', required=False, max_length=20),
            ColumnValidationRule('folio_pago', required=False, max_length=50),
            ColumnValidationRule('cliente', required=True, min_length=1, max_length=255),
            ColumnValidationRule('importe_pagado', required=True, data_type=float, min_value=0),
            ColumnValidationRule('uuid_factura_relacionada', required=False, pattern=r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
        ]
        
        # Reglas para pedidos
        self.validation_rules['pedidos'] = [
            ColumnValidationRule('folio_factura', required=True, data_type=int),
            ColumnValidationRule('pedido', required=True, min_length=1, max_length=50),
            ColumnValidationRule('material', required=True, min_length=1, max_length=255),
            ColumnValidationRule('kg', required=True, data_type=float, min_value=0),
            ColumnValidationRule('precio_unitario', required=False, data_type=float, min_value=0),
            ColumnValidationRule('importe_sin_iva', required=False, data_type=float, min_value=0),
            ColumnValidationRule('dias_credito', required=False, data_type=int, min_value=0, max_value=365),
            ColumnValidationRule('fecha_factura', required=False, data_type=datetime)
        ]
    
    def validate_dataframe(
        self, 
        df: pd.DataFrame, 
        sheet_type: str,
        custom_rules: Optional[List[ColumnValidationRule]] = None
    ) -> ValidationResult:
        """Valida un DataFrame según las reglas configuradas"""
        
        errors = []
        warnings = []
        cleaned_df = df.copy()
        
        # Obtener reglas de validación
        rules = custom_rules or self.validation_rules.get(sheet_type, [])
        
        if not rules:
            warnings.append(f"No validation rules found for sheet type: {sheet_type}")
            return ValidationResult(
                is_valid=True,
                errors=errors,
                warnings=warnings,
                cleaned_data=cleaned_df,
                validation_stats=self._calculate_stats(cleaned_df)
            )
        
        # Validar cada columna según las reglas
        for rule in rules:
            column_errors, column_warnings = self._validate_column(cleaned_df, rule)
            errors.extend(column_errors)
            warnings.extend(column_warnings)
        
        # Limpiar datos según el nivel de validación
        if self.validation_level in [ValidationLevel.MODERATE, ValidationLevel.LENIENT]:
            cleaned_df = self._clean_dataframe(cleaned_df, rules)
        
        # Determinar si los datos son válidos
        is_valid = len(errors) == 0 or (
            len(errors) <= 5 and self.validation_level == ValidationLevel.LENIENT
        )
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            cleaned_data=cleaned_df,
            validation_stats=self._calculate_stats(cleaned_df)
        )
    
    def _validate_column(self, df: pd.DataFrame, rule: ColumnValidationRule) -> Tuple[List[str], List[str]]:
        """Valida una columna específica"""
        errors = []
        warnings = []
        
        column_name = rule.column_name
        
        # Verificar si la columna existe
        if column_name not in df.columns:
            if rule.required:
                errors.append(f"Required column '{column_name}' is missing")
            else:
                warnings.append(f"Optional column '{column_name}' is missing")
            return errors, warnings
        
        column_data = df[column_name]
        null_count = column_data.isnull().sum()
        total_count = len(column_data)
        
        # Validar valores requeridos
        if rule.required and null_count > 0:
            if self.validation_level == ValidationLevel.STRICT:
                errors.append(f"Column '{column_name}' has {null_count} null values but is required")
            else:
                warnings.append(f"Column '{column_name}' has {null_count} null values but is required")
        
        # Validar tipo de datos
        if rule.data_type and null_count < total_count:
            type_errors = self._validate_data_type(column_data, rule.data_type, column_name)
            errors.extend(type_errors)
        
        # Validar longitud para strings
        if rule.min_length or rule.max_length:
            length_errors = self._validate_length(column_data, rule, column_name)
            errors.extend(length_errors)
        
        # Validar valores numéricos
        if rule.min_value is not None or rule.max_value is not None:
            range_errors = self._validate_numeric_range(column_data, rule, column_name)
            errors.extend(range_errors)
        
        # Validar valores permitidos
        if rule.allowed_values:
            allowed_errors = self._validate_allowed_values(column_data, rule.allowed_values, column_name)
            errors.extend(allowed_errors)
        
        # Validar patrón regex
        if rule.pattern:
            pattern_errors = self._validate_pattern(column_data, rule.pattern, column_name)
            errors.extend(pattern_errors)
        
        # Validación personalizada
        if rule.custom_validator:
            custom_errors = self._validate_custom(column_data, rule.custom_validator, column_name)
            errors.extend(custom_errors)
        
        return errors, warnings
    
    def _validate_data_type(self, column_data: pd.Series, expected_type: type, column_name: str) -> List[str]:
        """Valida el tipo de datos de una columna"""
        errors = []
        
        non_null_data = column_data.dropna()
        
        for idx, value in non_null_data.items():
            if expected_type == datetime:
                if not isinstance(value, (datetime, date)):
                    try:
                        pd.to_datetime(value)
                    except:
                        errors.append(f"Row {idx}: Column '{column_name}' value '{value}' is not a valid date")
            
            elif expected_type == float:
                if not isinstance(value, (int, float, np.number)):
                    try:
                        float(value)
                    except:
                        errors.append(f"Row {idx}: Column '{column_name}' value '{value}' is not a valid number")
            
            elif expected_type == int:
                if not isinstance(value, (int, np.integer)):
                    try:
                        int(float(value))
                    except:
                        errors.append(f"Row {idx}: Column '{column_name}' value '{value}' is not a valid integer")
        
        return errors
    
    def _validate_length(self, column_data: pd.Series, rule: ColumnValidationRule, column_name: str) -> List[str]:
        """Valida la longitud de valores string"""
        errors = []
        
        non_null_data = column_data.dropna()
        
        for idx, value in non_null_data.items():
            str_value = str(value)
            
            if rule.min_length and len(str_value) < rule.min_length:
                errors.append(f"Row {idx}: Column '{column_name}' value is too short (min: {rule.min_length})")
            
            if rule.max_length and len(str_value) > rule.max_length:
                errors.append(f"Row {idx}: Column '{column_name}' value is too long (max: {rule.max_length})")
        
        return errors
    
    def _validate_numeric_range(self, column_data: pd.Series, rule: ColumnValidationRule, column_name: str) -> List[str]:
        """Valida el rango de valores numéricos"""
        errors = []
        
        non_null_data = column_data.dropna()
        
        for idx, value in non_null_data.items():
            try:
                num_value = float(value)
                
                if rule.min_value is not None and num_value < rule.min_value:
                    errors.append(f"Row {idx}: Column '{column_name}' value {num_value} is below minimum {rule.min_value}")
                
                if rule.max_value is not None and num_value > rule.max_value:
                    errors.append(f"Row {idx}: Column '{column_name}' value {num_value} is above maximum {rule.max_value}")
            
            except (ValueError, TypeError):
                errors.append(f"Row {idx}: Column '{column_name}' value '{value}' is not numeric")
        
        return errors
    
    def _validate_allowed_values(self, column_data: pd.Series, allowed_values: List[Any], column_name: str) -> List[str]:
        """Valida valores permitidos"""
        errors = []
        
        non_null_data = column_data.dropna()
        
        for idx, value in non_null_data.items():
            if value not in allowed_values:
                errors.append(f"Row {idx}: Column '{column_name}' value '{value}' is not in allowed values: {allowed_values}")
        
        return errors
    
    def _validate_pattern(self, column_data: pd.Series, pattern: str, column_name: str) -> List[str]:
        """Valida patrón regex"""
        errors = []
        
        non_null_data = column_data.dropna()
        
        for idx, value in non_null_data.items():
            if not re.match(pattern, str(value)):
                errors.append(f"Row {idx}: Column '{column_name}' value '{value}' does not match required pattern")
        
        return errors
    
    def _validate_custom(self, column_data: pd.Series, validator: callable, column_name: str) -> List[str]:
        """Valida usando función personalizada"""
        errors = []
        
        non_null_data = column_data.dropna()
        
        for idx, value in non_null_data.items():
            try:
                if not validator(value):
                    errors.append(f"Row {idx}: Column '{column_name}' value '{value}' failed custom validation")
            except Exception as e:
                errors.append(f"Row {idx}: Column '{column_name}' custom validation error: {str(e)}")
        
        return errors
    
    def _clean_dataframe(self, df: pd.DataFrame, rules: List[ColumnValidationRule]) -> pd.DataFrame:
        """Limpia el DataFrame según las reglas"""
        cleaned_df = df.copy()
        
        for rule in rules:
            column_name = rule.column_name
            
            if column_name not in cleaned_df.columns:
                continue
            
            # Limpiar valores nulos según el tipo
            if rule.data_type == datetime:
                # Convertir strings a datetime
                cleaned_df[column_name] = pd.to_datetime(cleaned_df[column_name], errors='coerce')
            
            elif rule.data_type == float:
                # Convertir a float
                cleaned_df[column_name] = pd.to_numeric(cleaned_df[column_name], errors='coerce')
            
            elif rule.data_type == int:
                # Convertir a int
                cleaned_df[column_name] = pd.to_numeric(cleaned_df[column_name], errors='coerce').astype('Int64')
            
            # Truncar strings largos
            if rule.max_length:
                string_columns = cleaned_df.select_dtypes(include=['object']).columns
                if column_name in string_columns:
                    cleaned_df[column_name] = cleaned_df[column_name].astype(str).str[:rule.max_length]
        
        return cleaned_df
    
    def _calculate_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula estadísticas del DataFrame"""
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "null_counts": df.isnull().sum().to_dict(),
            "data_types": df.dtypes.to_dict(),
            "memory_usage": df.memory_usage(deep=True).sum(),
            "duplicate_rows": df.duplicated().sum()
        }
    
    def validate_file_structure(self, file_data: Dict[str, pd.DataFrame]) -> Dict[str, ValidationResult]:
        """Valida la estructura completa de un archivo"""
        results = {}
        
        # Validar que existan las hojas requeridas
        required_sheets = ['facturacion', 'cobranza', 'pedidos']
        missing_sheets = [sheet for sheet in required_sheets if sheet not in file_data]
        
        if missing_sheets:
            logger.warning(f"Missing required sheets: {missing_sheets}")
        
        # Validar cada hoja
        for sheet_name, df in file_data.items():
            try:
                result = self.validate_dataframe(df, sheet_name)
                results[sheet_name] = result
                
                if not result.is_valid:
                    logger.error(f"Validation failed for sheet '{sheet_name}': {len(result.errors)} errors")
                
                if result.warnings:
                    logger.warning(f"Validation warnings for sheet '{sheet_name}': {len(result.warnings)} warnings")
                    
            except Exception as e:
                logger.error(f"Error validating sheet '{sheet_name}': {str(e)}")
                results[sheet_name] = ValidationResult(
                    is_valid=False,
                    errors=[f"Validation error: {str(e)}"],
                    warnings=[]
                )
        
        return results

# Funciones de utilidad para validación específica
def validate_uuid(value: Any) -> bool:
    """Valida formato UUID"""
    import re
    uuid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    return isinstance(value, str) and bool(re.match(uuid_pattern, value))

def validate_positive_number(value: Any) -> bool:
    """Valida que el valor sea un número positivo"""
    try:
        num = float(value)
        return num >= 0
    except (ValueError, TypeError):
        return False

def validate_date_range(value: Any) -> bool:
    """Valida que la fecha esté en un rango razonable"""
    try:
        if isinstance(value, (datetime, date)):
            date_obj = value
        else:
            date_obj = pd.to_datetime(value)
        
        # Verificar que la fecha esté entre 2020 y 2030
        return 2020 <= date_obj.year <= 2030
    except:
        return False
