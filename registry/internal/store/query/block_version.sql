-- name: CreateBlockVersion :one
INSERT INTO
    public.block_versions (
        block_id,
        version,
        specification,
        documentation_url,
        thumbnail_url,
        catalog_url,
        docker_image
    )
VALUES
    (
        $1,
        $2,
        $3,
        $4,
        $5,
        $6,
        $7
    ) RETURNING *;

-- name: GetBlockAllVersionByName :many
SELECT
    b.id,
    b.name,
    b.type,
    b.kind,
    bv.version,
    bv.specification,
    bv.documentation_url,
    bv.thumbnail_url,
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
    bv.thumbnail_url,
    bv.docker_image,
    bv.created_at,
    bv.updated_at,
    bv.catalog_url
FROM public.block_versions bv
    INNER JOIN public.blocks b
    ON bv.block_id = b.id
WHERE b.name = $1 and bv.version = $2;
