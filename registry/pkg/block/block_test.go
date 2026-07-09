package block

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"reflect"
	"testing"
	"time"

	mock_store "github.com/pixxelhq/clay-framework/registry/internal/store/mock"
	store "github.com/pixxelhq/clay-framework/registry/internal/store/sqlc"
	rerr "github.com/pixxelhq/clay-framework/registry/pkg/error"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"go.uber.org/mock/gomock"
)

var reqBlock = &Block{
	Name:             "Test Block",
	Kind:             "example",
	Type:             "exampleType",
	Version:          "1.0.0",
	DocumentationURL: "http://example.com",
	DockerImage:      "example/image:latest",
	Specification: &Specification{
		Version:     "1.0.0",
		Title:       "Test Specification",
		Description: "This is a test specification",
		Author:      "Author Name",
		Tags:        []string{"tag1", "tag2"},
		Parameters:  json.RawMessage(`{}`),
		Inputs:      json.RawMessage(`{}`),
		Outputs:     json.RawMessage(`{}`),
		Build:       json.RawMessage(`{}`),
	},
}

func TestCreate(t *testing.T) {
	ctrl := gomock.NewController(t)
	defer ctrl.Finish()

	mockStore := mock_store.NewMockStore(ctrl)
	service := New(mockStore)

	tests := []struct {
		name          string
		input         *Block
		mockSetup     func()
		expectedError error
	}{
		{
			name:  "successful creation",
			input: reqBlock,
			mockSetup: func() {
				mockStore.EXPECT().ExecWithTx(gomock.Any(), gomock.Any()).
					DoAndReturn(func(ctx context.Context, fn func(q store.Querier) (interface{}, error)) (interface{}, error) {
						q := mockStore

						upsertedBlock := store.Block{
							ID:   uuid.New(),
							Name: "Test Block",
							Kind: "example",
							Type: "exampleType",
						}

						q.EXPECT().UpsertBlock(gomock.Any(), store.UpsertBlockParams{
							Name: "Test Block",
							Kind: "example",
							Type: "exampleType",
						}).Return(upsertedBlock, nil)

						specByte, _ := json.Marshal(&Specification{
							Version:     "1.0.0",
							Title:       "Test Specification",
							Description: "This is a test specification",
							Author:      "Author Name",
							Tags:        []string{"tag1", "tag2"},
							Parameters:  json.RawMessage(`{}`),
							Inputs:      json.RawMessage(`{}`),
							Outputs:     json.RawMessage(`{}`),
							Build:       json.RawMessage(`{}`),
						})

						bv := store.BlockVersion{
							ID:               uuid.New(),
							Version:          "1.0.0",
							BlockID:          upsertedBlock.ID,
							Specification:    specByte,
							DocumentationUrl: sql.NullString{String: "http://example.com", Valid: true},
							Catalog:          json.RawMessage("{}"),
							DockerImage:      sql.NullString{String: "example/image:latest", Valid: true},
						}

						q.EXPECT().CreateBlockVersion(gomock.Any(), store.CreateBlockVersionParams{
							BlockID:          upsertedBlock.ID,
							Version:          "1.0.0",
							Specification:    specByte,
							DocumentationUrl: sql.NullString{String: "http://example.com", Valid: true},
							Catalog:          json.RawMessage("{}"),
							DockerImage:      sql.NullString{String: "example/image:latest", Valid: true},
						}).Return(bv, nil)

						return fn(q)
					})
			},
			expectedError: nil,
		},
		{
			name: "error on upsert block",
			input: &Block{
				Name: "Test Block",
				Kind: "example",
				Type: "exampleType",
			},
			mockSetup: func() {
				mockStore.EXPECT().ExecWithTx(gomock.Any(), gomock.Any()).
					DoAndReturn(func(ctx context.Context, fn func(q store.Querier) (interface{}, error)) (interface{}, error) {
						q := mockStore

						q.EXPECT().UpsertBlock(gomock.Any(), store.UpsertBlockParams{
							Name: "Test Block",
							Kind: "example",
							Type: "exampleType",
						}).Return(store.Block{}, errors.New("upsert error"))

						return fn(q)
					})
			},
			expectedError: errors.New("upsert error"),
		},
		{
			name: "error on create block version",
			input: &Block{
				Name:             "Test Block",
				Kind:             "example",
				Type:             "exampleType",
				Specification:    &Specification{},
				Version:          "1.0.0",
				DocumentationURL: "http://example.com",
				DockerImage:      "example/image:latest",
			},
			mockSetup: func() {
				mockStore.EXPECT().ExecWithTx(gomock.Any(), gomock.Any()).
					DoAndReturn(func(ctx context.Context, fn func(q store.Querier) (interface{}, error)) (interface{}, error) {
						q := mockStore

						upsertedBlock := store.Block{
							ID:   uuid.New(),
							Name: "Test Block",
							Kind: "example",
							Type: "exampleType",
						}

						q.EXPECT().UpsertBlock(gomock.Any(), store.UpsertBlockParams{
							Name: "Test Block",
							Kind: "example",
							Type: "exampleType",
						}).Return(upsertedBlock, nil)

						specByte, _ := json.Marshal(&Specification{})

						q.EXPECT().CreateBlockVersion(gomock.Any(), store.CreateBlockVersionParams{
							BlockID:          upsertedBlock.ID,
							Version:          "1.0.0",
							Specification:    specByte,
							DocumentationUrl: sql.NullString{String: "http://example.com", Valid: true},
							Catalog:          json.RawMessage("{}"),
							DockerImage:      sql.NullString{String: "example/image:latest", Valid: true},
						}).Return(store.BlockVersion{}, errors.New("create block version error"))

						return fn(q)
					})
			},
			expectedError: &rerr.RegistryError{Err: errors.New("create block version error"),
				Code: rerr.ErrInternal},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tt.mockSetup()
			resp, err := service.Create(context.Background(), tt.input)
			if tt.expectedError != nil {
				assert.Error(t, err)
				assert.Equal(t, tt.expectedError.Error(), err.Error())
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, resp)
			}
		})
	}
}

func TestGetBlocksWithLatestVersion(t *testing.T) {
	ctrl := gomock.NewController(t)
	defer ctrl.Finish()

	mockStore := mock_store.NewMockStore(ctrl)
	sampleUUID := uuid.New()
	sampleTime := time.Now()
	tests := []struct {
		name           string
		mockSetup      func()
		expectedBlocks []*Block
		expectedError  error
	}{
		{
			name: "should return the blocks with latest versions",
			mockSetup: func() {
				mockStore.EXPECT().GetAllBlocks(gomock.Any()).Return([]store.Block{
					{
						ID:        sampleUUID,
						Name:      "Block1",
						Kind:      "example",
						Type:      "exampleType",
						CreatedAt: sql.NullTime{Time: sampleTime},
						UpdatedAt: sql.NullTime{Time: sampleTime},
					},
				}, nil)
				mockStore.EXPECT().GetBlockAllVersionByName(gomock.Any(), gomock.Any()).Return([]store.GetBlockAllVersionByNameRow{
					{
						ID:               sampleUUID,
						Name:             "Block1",
						Version:          "v1.0",
						Specification:    json.RawMessage(`{"apiVersion":"1.0","title":"Test Block"}`),
						DocumentationUrl: sql.NullString{String: "http://example.com", Valid: true},
						DockerImage:      sql.NullString{String: "example/image", Valid: true},
						CreatedAt:        sql.NullTime{Time: sampleTime},
						UpdatedAt:        sql.NullTime{Time: sampleTime},
					},
				}, nil)
			},
			expectedBlocks: []*Block{
				{
					ID:               sampleUUID.String(),
					Name:             "Block1",
					Version:          "v1.0",
					Specification:    &Specification{Version: "1.0", Title: "Test Block"},
					DocumentationURL: "http://example.com",
					DockerImage:      "example/image",
					CreatedAt:        sampleTime,
					UpdatedAt:        sampleTime,
				},
			},
			expectedError: nil,
		},
		{
			name: "should return empty list if there is not block found",
			mockSetup: func() {
				mockStore.EXPECT().GetAllBlocks(gomock.Any()).Return([]store.Block{}, nil)
			},
			expectedBlocks: []*Block{},
			expectedError:  nil,
		},
		{
			name: "should return error when db call fails",
			mockSetup: func() {
				mockStore.EXPECT().GetAllBlocks(gomock.Any()).Return(nil, errors.New("some error"))
			},
			expectedBlocks: nil,
			expectedError:  errors.New("some error"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tt.mockSetup()
			bs := &block{store: mockStore}

			blocks, err := bs.GetBlocksWithLatestVersion(context.Background())
			if tt.expectedBlocks != nil {
				assert.Equal(t, len(tt.expectedBlocks), len(blocks))
				assert.Equal(t, true, reflect.DeepEqual(tt.expectedBlocks, blocks))
				assert.NoError(t, err)
			}

			if tt.expectedError != nil {
				assert.Error(t, err)
				assert.Equal(t, tt.expectedError.Error(), err.Error())
			}
		})
	}
}

func TestGetBlockByName(t *testing.T) {
	ctrl := gomock.NewController(t)
	defer ctrl.Finish()

	mockStore := mock_store.NewMockStore(ctrl)
	sampleUUID := uuid.New()
	sampleTime := time.Now()
	tests := []struct {
		name           string
		blockName      string
		mockSetup      func()
		expectedBlocks []*Block
		expectedError  error
	}{
		{
			name:      "should return the block by name",
			blockName: "Test_Block",
			mockSetup: func() {
				mockStore.EXPECT().GetBlockAllVersionByName(gomock.Any(), gomock.Any()).Return([]store.GetBlockAllVersionByNameRow{
					{
						ID:               sampleUUID,
						Name:             "Test_Block",
						Version:          "1.0.0",
						Specification:    json.RawMessage(`{"apiVersion":"1.0","title":"Test Block"}`),
						DocumentationUrl: sql.NullString{String: "http://example.com", Valid: true},
						DockerImage:      sql.NullString{String: "example/image", Valid: true},
						CreatedAt:        sql.NullTime{Time: sampleTime},
						UpdatedAt:        sql.NullTime{Time: sampleTime},
					},
				}, nil)
			},
			expectedBlocks: []*Block{
				{
					ID:               sampleUUID.String(),
					Name:             "Test_Block",
					Version:          "1.0.0",
					Specification:    &Specification{Version: "1.0", Title: "Test Block"},
					DocumentationURL: "http://example.com",
					DockerImage:      "example/image",
					CreatedAt:        sampleTime,
					UpdatedAt:        sampleTime,
				},
			},
			expectedError: nil,
		},
		{
			name:      "should return empty list if no block found",
			blockName: "Nonexistent Block",
			mockSetup: func() {
				mockStore.EXPECT().GetBlockAllVersionByName(gomock.Any(), gomock.Any()).Return([]store.GetBlockAllVersionByNameRow{}, nil)
			},
			expectedBlocks: []*Block{},
			expectedError:  nil,
		},
		{
			name:      "should return error when db call fails",
			blockName: "Test Block",
			mockSetup: func() {
				mockStore.EXPECT().GetBlockAllVersionByName(gomock.Any(), gomock.Any()).Return(nil, errors.New("some error"))
			},
			expectedBlocks: nil,
			expectedError:  errors.New("some error"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tt.mockSetup()
			bs := &block{store: mockStore}

			blocks, err := bs.GetBlockByName(context.Background(), tt.blockName)
			if tt.expectedBlocks != nil {
				assert.Equal(t, true, reflect.DeepEqual(tt.expectedBlocks, blocks))
				assert.NoError(t, err)
			}

			if tt.expectedError != nil {
				assert.Error(t, err)
				assert.Equal(t, tt.expectedError.Error(), err.Error())
			}
		})
	}
}

func TestGetBlockByNameAndVersion(t *testing.T) {
	ctrl := gomock.NewController(t)
	defer ctrl.Finish()

	mockStore := mock_store.NewMockStore(ctrl)
	sampleUUID := uuid.New()
	sampleTime := time.Now()
	tests := []struct {
		name          string
		blockName     string
		version       string
		mockSetup     func()
		expectedBlock *Block
		expectedError error
	}{
		{
			name:      "should return block for valid request",
			blockName: "Test Block",
			version:   "1.0.0",
			mockSetup: func() {
				mockStore.EXPECT().GetBlockByNameAndVersion(gomock.Any(), gomock.Any()).Times(1).Return(store.GetBlockByNameAndVersionRow{
					ID:               sampleUUID,
					Name:             "Test Block",
					Version:          "1.0.0",
					Specification:    json.RawMessage(`{"apiVersion":"1.0","title":"Test Block"}`),
					DocumentationUrl: sql.NullString{String: "http://example.com", Valid: true},
					DockerImage:      sql.NullString{String: "example/image", Valid: true},
					Catalog:          json.RawMessage(`{"assets":[]}`),
					CreatedAt:        sql.NullTime{Time: sampleTime},
					UpdatedAt:        sql.NullTime{Time: sampleTime},
				}, nil)
			},
			expectedBlock: &Block{
				ID:               sampleUUID.String(),
				Name:             "Test Block",
				Version:          "1.0.0",
				Specification:    &Specification{Version: "1.0", Title: "Test Block"},
				DocumentationURL: "http://example.com",
				DockerImage:      "example/image",
				Catalog:          json.RawMessage(`{"assets":[]}`),
				CreatedAt:        sampleTime,
				UpdatedAt:        sampleTime,
			},
			expectedError: nil,
		},
		{
			name:      "should return error for store error",
			blockName: "Test Block",
			version:   "1.0.0",
			mockSetup: func() {
				mockStore.EXPECT().GetBlockByNameAndVersion(gomock.Any(), gomock.Any()).Times(1).Return(store.GetBlockByNameAndVersionRow{}, assert.AnError)
			},
			expectedBlock: nil,
			expectedError: &rerr.RegistryError{Code: rerr.ErrInternal, Err: assert.AnError},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tt.mockSetup()
			bs := &block{store: mockStore}

			block, err := bs.GetBlockByNameAndVersion(context.Background(), tt.blockName, tt.version)
			if tt.expectedBlock != nil {
				assert.Equal(t, tt.expectedBlock, block)
				assert.NoError(t, err)
			}

			if tt.expectedError != nil {
				assert.Error(t, err)
				assert.Equal(t, tt.expectedError.Error(), err.Error())
			}
		})
	}
}
