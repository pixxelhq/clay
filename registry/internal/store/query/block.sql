-- name: CreateBlock :one
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
    ) RETURNING *;