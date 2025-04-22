-- name: UpsertBlock :one
INSERT INTO 
    public.blocks (
        name,
        kind,
        type
    )
VALUES
    (
        $1,
        $2,
        $3
    ) 
ON CONFLICT(name) 
DO UPDATE SET 
    name = EXCLUDED.name
RETURNING *;

-- name: GetBlock :one
SELECT
    id,
    name,
    kind,   
    type,
    created_at,
    updated_at
FROM 
    public.blocks
WHERE 
    id = $1;

-- name: GetAllBlocks :many
SELECT
    id,
    name,
    kind,
    type,
    created_at,
    updated_at
FROM
    public.blocks;