-- name: CreateBlockVersion :one
INSERT INTO 
    public.block_versions (
        block_id,
        version,
        specification,
        documentation_url,
        docker_image
    )
VALUES
    (
        $1,
        $2,
        $3,
        $4,
        $5
    ) RETURNING *;

-- name: GetBlocksWithLatestVersion :many
SELECT distinct on (b.id)
    b.id,
    b.name,
    b.type,
    b.kind,
    bv.version,
    bv.specification,
    bv.documentation_url,
    bv.docker_image,
    bv.created_at,
    bv.updated_at
FROM public.block_versions bv 
    INNER JOIN public.blocks b
    ON bv.block_id = b.id
ORDER BY b.id, string_to_array(regexp_replace(bv.version, '^v', ''), '.')::int[] desc;

-- name: GetBlockAllVersionByName :many
SELECT
    b.id,
    b.name,
    b.type,
    b.kind,
    bv.version,
    bv.specification,
    bv.documentation_url,
    bv.docker_image,
    bv.created_at,
    bv.updated_at
FROM public.block_versions bv
    INNER JOIN public.blocks b
    ON bv.block_id = b.id
WHERE b.name = $1
ORDER BY b.id, bv.version desc;

-- name: GetBlockByNameAndVersion :one
SELECT
    b.id,
    b.name,
    bv.version,
    b.type,
    b.kind,
    bv.specification,
    bv.documentation_url,
    bv.docker_image,
    bv.created_at,
    bv.updated_at
FROM public.block_versions bv
    INNER JOIN public.blocks b
    ON bv.block_id = b.id
WHERE b.name = $1 and bv.version = $2;

-- name: GetLatestBlockByName :one
SELECT
    b.id,
    b.name,
    bv.version,
    b.type,
    b.kind,
    bv.specification,
    bv.documentation_url,
    bv.docker_image,
    bv.created_at,
    bv.updated_at
FROM public.block_versions bv
    INNER JOIN public.blocks b
    ON bv.block_id = b.id
WHERE b.name = $1
ORDER BY string_to_array(regexp_replace(bv.version, '^v', ''), '.')::int[] DESC
LIMIT 1;
