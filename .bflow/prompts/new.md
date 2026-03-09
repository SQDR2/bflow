# bflow-new

Use this workflow to create a new case draft from a natural-language test request.

The workflow should:

1. Read `.bflow/cases/templates/test-flow.template.yaml`.
2. Infer a clear case name and output file path under `.bflow/cases/`.
3. Fill any fields that are explicit in the request:
   - `base_url`
   - `goal`
   - `lifecycle`
   - `preconditions`
   - `credentials`
   - `assertions`
   - obvious `steps`
4. Leave uncertain `steps` empty instead of inventing them.
5. Set `lifecycle.stage` to `draft` and `lifecycle.ready_for_replay` to `false`.
6. Create or update the case file.
7. End by recommending `bflow-explore` as the next step.
