"""
PySpark transformation functions for the data pipeline.

In a real application, this would contain more complex transformations
using the full power of Spark's distributed computing capabilities.
"""
import os
import sys
import json
from typing import List, Dict, Any
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, lit, when, expr, udf
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, BooleanType, TimestampType


def create_spark_session(app_name: str, master_url: str = "local[*]") -> SparkSession:
    """
    Create and configure a SparkSession

    Args:
        app_name: Name of the Spark application
        master_url: Spark master URL

    Returns:
        Configured SparkSession
    """
    return (SparkSession.builder
            .appName(app_name)
            .master(master_url)
            .config("spark.sql.execution.arrow.pyspark.enabled", "true")
            .config("spark.driver.memory", "1g")
            .getOrCreate())


def load_data_as_dataframe(spark: SparkSession, data: List[Dict[str, Any]]) -> DataFrame:
    """
    Load data from a list of dictionaries into a Spark DataFrame

    Args:
        spark: SparkSession
        data: List of data records

    Returns:
        Spark DataFrame
    """
    # Define schema based on the first record
    if not data:
        return None

    # Create a sample record to infer schema
    sample = data[0]
    schema_fields = []

    for key, value in sample.items():
        if isinstance(value, str):
            schema_fields.append(StructField(key, StringType(), True))
        elif isinstance(value, float):
            schema_fields.append(StructField(key, DoubleType(), True))
        elif isinstance(value, int):
            schema_fields.append(StructField(key, IntegerType(), True))
        elif isinstance(value, bool):
            schema_fields.append(StructField(key, BooleanType(), True))
        else:
            # Default to string for other types
            schema_fields.append(StructField(key, StringType(), True))

    schema = StructType(schema_fields)

    # Create DataFrame
    return spark.createDataFrame(data, schema)


def process_dataframe(df: DataFrame) -> DataFrame:
    """
    Process the DataFrame with various transformations

    Args:
        df: Input DataFrame

    Returns:
        Processed DataFrame
    """
    # Check if the required columns exist
    required_cols = ["value", "quantity", "category"]
    if not all(col_name in df.columns for col_name in required_cols):
        raise ValueError(
            f"Input DataFrame must contain the columns: {required_cols}")

    # Calculate derived columns
    processed_df = df.withColumn("total_value", col("value") * col("quantity"))

    # Add category-based pricing tier
    processed_df = processed_df.withColumn(
        "pricing_tier",
        when(col("total_value") > 5000, "premium")
        .when(col("total_value") > 1000, "standard")
        .otherwise("basic")
    )

    # Add processing metadata
    processed_df = processed_df.withColumn("processed_by", lit("spark"))
    processed_df = processed_df.withColumn(
        "processing_timestamp", expr("current_timestamp()"))

    # Apply category-specific calculations
    processed_df = processed_df.withColumn(
        "discount_factor",
        when(col("category") == "A", 0.9)
        .when(col("category") == "B", 0.85)
        .when(col("category") == "C", 0.8)
        .otherwise(0.95)
    )

    processed_df = processed_df.withColumn(
        "discounted_value",
        col("total_value") * col("discount_factor")
    )

    return processed_df


def aggregate_by_category(df: DataFrame) -> DataFrame:
    """
    Aggregate data by category

    Args:
        df: Input DataFrame

    Returns:
        Aggregated DataFrame
    """
    return df.groupBy("category").agg(
        expr("count(*) as record_count"),
        expr("sum(total_value) as total_value_sum"),
        expr("avg(total_value) as total_value_avg"),
        expr("min(total_value) as total_value_min"),
        expr("max(total_value) as total_value_max")
    )


def dataframe_to_dict_list(df: DataFrame) -> List[Dict[str, Any]]:
    """
    Convert a Spark DataFrame to a list of dictionaries

    Args:
        df: Input DataFrame

    Returns:
        List of dictionaries
    """
    return [row.asDict() for row in df.collect()]


def run_spark_pipeline(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run the complete Spark processing pipeline

    Args:
        data: Input data as a list of dictionaries

    Returns:
        Processed data as a list of dictionaries
    """
    # Create Spark session
    spark = create_spark_session("DataPipeline")

    try:
        # Load data
        df = load_data_as_dataframe(spark, data)

        # Process data
        processed_df = process_dataframe(df)

        # Convert back to list of dictionaries
        result = dataframe_to_dict_list(processed_df)

        return result

    finally:
        # Always stop the Spark session
        spark.stop()
