# Copyright (c) Microsoft. All rights reserved.

"""Schema-Based Query Generator Workflow.

This workflow generates SQL queries based on:
1. Database schema (table definitions)
2. Natural language query description

Workflow steps:
1. Schema Parser - Analyzes the database schema
2. Query Generator - Generates SQL based on schema and description
3. Parallel Validation (Fan-out):
   - Syntax Checker - Validates SQL syntax
   - Schema Validator - Checks query matches schema
   - Performance Reviewer - Reviews query performance
4. Query Refiner - Refines query based on feedback
5. Documentation Generator - Creates usage documentation

Example input:
Schema:
```
CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100), email VARCHAR(100));
CREATE TABLE orders (id INT PRIMARY KEY, user_id INT, total DECIMAL(10,2), created_at TIMESTAMP);
```
Query: "Find all users who placed orders over $100 in the last month"
"""

from agent_framework import (
    AgentExecutorResponse,
    ChatAgent,
    Executor,
    WorkflowBuilder,
    WorkflowContext,
    handler,
)
from agent_framework.azure import AzureOpenAIChatClient
from typing_extensions import Never

# Create Azure OpenAI chat client for all agents
chat_client = AzureOpenAIChatClient()


# Step 1: Schema Parser
schema_parser = ChatAgent(
    name="SchemaParser",
    description="Analyzes database schema structure",
    chat_client=chat_client,
    instructions="""You are a database schema analyst. Analyze the provided schema and query description:

Extract:
- Table names and their columns
- Primary keys and foreign keys
- Relationships between tables
- Data types
- Which tables are needed for the query

Output a clear analysis (under 150 words) that will help the query generator understand the schema structure.
Format: 
Tables: [list]
Relationships: [describe joins needed]
Required tables: [tables needed for this query]
""",
)

# Step 2: Query Generator
query_generator = ChatAgent(
    name="QueryGenerator",
    description="Generates SQL query from schema analysis and description",
    chat_client=chat_client,
    instructions="""You are an expert SQL query writer. Based on the schema analysis provided:

Generate a SQL SELECT query that:
- Uses the correct table and column names from the schema
- Includes proper JOINs if multiple tables are needed
- Has appropriate WHERE clauses
- Uses correct data types for comparisons
- Follows SQL best practices
- Is optimized for performance

Output:
1. The SQL query (clean, formatted)
2. Brief explanation (1-2 sentences)

Total response under 200 words.
""",
)

# Step 3a: Syntax Checker (Parallel validation)
syntax_checker = ChatAgent(
    name="SyntaxChecker",
    description="Validates SQL syntax",
    chat_client=chat_client,
    instructions="""You are a SQL syntax validator. Check the generated query:

Verify:
- Correct SELECT syntax
- Proper JOIN syntax
- Valid WHERE clause
- Correct use of parentheses
- No syntax errors

Response format (under 80 words):
Status: ✓ VALID or ✗ INVALID
Issues: [list or "None"]
""",
)

# Step 3b: Schema Validator (Parallel validation)
schema_validator = ChatAgent(
    name="SchemaValidator",
    description="Validates query matches schema",
    chat_client=chat_client,
    instructions="""You are a schema validation expert. Check if the query matches the provided schema:

Verify:
- All table names exist in schema
- All column names exist in their tables
- JOINs use correct foreign keys
- Data types are used correctly
- No references to non-existent entities

Response format (under 80 words):
Status: ✓ VALID or ✗ INVALID
Mismatches: [list or "None"]
""",
)

# Step 3c: Performance Reviewer (Parallel validation)
performance_reviewer = ChatAgent(
    name="PerformanceReviewer",
    description="Reviews query performance",
    chat_client=chat_client,
    instructions="""You are a query performance expert. Review the query for performance:

Check for:
- Efficient use of indexes
- Appropriate WHERE clauses
- Proper JOIN order
- Avoiding SELECT *
- Use of LIMIT where appropriate

Response format (under 80 words):
Performance: GOOD/ACCEPTABLE/NEEDS WORK
Suggestions: [list or "None"]
""",
)


# Step 4: Validation Aggregator (Custom Executor for Fan-in)
class ValidationAggregator(Executor):
    """Aggregates validation results from parallel checkers."""

    @handler
    async def aggregate(
        self,
        results: list[AgentExecutorResponse],
        ctx: WorkflowContext[str],
    ) -> None:
        """Combine all validation results into a summary."""
        # Extract text from each agent response
        validations: list[str] = []
        for r in results:
            validator_name = r.executor_id.replace("_", " ").title()
            text = r.agent_run_response.text
            validations.append(f"**{validator_name}**:\n{text}")
        
        # Combine all validation feedback
        combined = "\n\n".join(validations)
        
        summary = f"=== VALIDATION SUMMARY ===\n\n{combined}\n\n"
        await ctx.send_message(summary)


validation_aggregator = ValidationAggregator(id="validation_aggregator")


# Step 5: Query Refiner
query_refiner = ChatAgent(
    name="QueryRefiner",
    description="Refines query based on validation feedback",
    chat_client=chat_client,
    instructions="""You are a query refinement expert. Review the validation results:

If there are issues:
- Fix syntax errors
- Correct schema mismatches
- Improve performance based on suggestions

If everything is valid:
- Add helpful comments
- Ensure formatting is clean
- Add any minor optimizations

Output:
1. Final SQL query (clean, formatted, with comments)
2. Summary of changes made (2-3 sentences)

Total response under 200 words.
""",
)

# Step 6: Final SQL Output Generator
documentation_generator = ChatAgent(
    name="FinalSQLOutput",
    description="Outputs only the final clean SQL query",
    chat_client=chat_client,
    instructions="""You are a SQL formatter. Output ONLY the final, clean SQL query - nothing else.

Requirements:
- Extract the final SQL query from the previous conversation
- Format it cleanly with proper indentation
- Do NOT include any explanations, comments, or descriptions
- Do NOT wrap it in code blocks or markdown
- Do NOT add any text before or after the SQL
- Just output the pure SQL statement

Example output:
SELECT s.first_name, s.last_name, s.email
FROM students s
JOIN enrollments e ON s.student_id = e.student_id
JOIN courses c ON e.course_id = c.course_id
WHERE c.course_name = 'Mathematics';
""",
)

# Build the workflow with fan-out/fan-in pattern
workflow = (
    WorkflowBuilder()
    .set_start_executor(schema_parser)
    .add_edge(schema_parser, query_generator)
    # Fan-out to parallel validation, then fan-in
    .add_fan_out_edges(query_generator, [syntax_checker, schema_validator, performance_reviewer])
    .add_fan_in_edges([syntax_checker, schema_validator, performance_reviewer], validation_aggregator)
    # Sequential flow after validation
    .add_edge(validation_aggregator, query_refiner)
    .add_edge(query_refiner, documentation_generator)
    .build()
)


def main():
    """Launch the query generator workflow in DevUI."""
    import logging

    from agent_framework.devui import serve

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    logger.info("Starting Schema-Based Query Generator Workflow")
    logger.info("Available at: http://localhost:8090")
    logger.info("\nExample input:")
    logger.info("Schema:")
    logger.info("CREATE TABLE users (id INT, name VARCHAR(100), email VARCHAR(100));")
    logger.info("CREATE TABLE orders (id INT, user_id INT, total DECIMAL(10,2), created_at TIMESTAMP);")
    logger.info("\nQuery: Find all users who placed orders over $100 in the last month")

    # Launch server with the workflow
    serve(entities=[workflow], port=8090, auto_open=True)


if __name__ == "__main__":
    main()
