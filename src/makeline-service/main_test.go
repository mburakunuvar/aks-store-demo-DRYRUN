package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"

	"github.com/gin-gonic/gin"
)

// mockOrderRepo is a test double that implements the OrderRepo interface.
type mockOrderRepo struct {
	getPendingOrdersFunc func() ([]Order, error)
	getOrderFunc         func(id string) (Order, error)
	insertOrdersFunc     func(orders []Order) error
	updateOrderFunc      func(order Order) error
}

func (m *mockOrderRepo) GetPendingOrders() ([]Order, error) {
	if m.getPendingOrdersFunc != nil {
		return m.getPendingOrdersFunc()
	}
	return nil, nil
}

func (m *mockOrderRepo) GetOrder(id string) (Order, error) {
	if m.getOrderFunc != nil {
		return m.getOrderFunc(id)
	}
	return Order{}, nil
}

func (m *mockOrderRepo) InsertOrders(orders []Order) error {
	if m.insertOrdersFunc != nil {
		return m.insertOrdersFunc(orders)
	}
	return nil
}

func (m *mockOrderRepo) UpdateOrder(order Order) error {
	if m.updateOrderFunc != nil {
		return m.updateOrderFunc(order)
	}
	return nil
}

// setupTestRouter creates a gin router wired up with the provided repo mock.
// The route definitions mirror those in main() so that the handlers under test
// are identical to production.
func setupTestRouter(repo OrderRepo) *gin.Engine {
	gin.SetMode(gin.TestMode)
	router := gin.New()
	orderService := NewOrderService(repo)
	router.Use(OrderMiddleware(orderService))
	router.GET("/order/fetch", fetchOrders)
	router.GET("/order/:id", getOrder)
	router.PUT("/order", updateOrder)
	// Inline health handler kept consistent with the anonymous handler in main().
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "ok",
			"version": os.Getenv("APP_VERSION"),
		})
	})
	return router
}

// --- NewOrderService ---

func TestNewOrderService(t *testing.T) {
	mock := &mockOrderRepo{}
	svc := NewOrderService(mock)
	if svc == nil {
		t.Fatal("expected non-nil OrderService")
	}
	if svc.repo != mock {
		t.Error("expected repo to match the provided mock")
	}
}

// --- OrderMiddleware ---

func TestOrderMiddleware(t *testing.T) {
	gin.SetMode(gin.TestMode)
	mock := &mockOrderRepo{}
	svc := NewOrderService(mock)

	router := gin.New()
	router.Use(OrderMiddleware(svc))
	router.GET("/test", func(c *gin.Context) {
		got, ok := c.MustGet("orderService").(*OrderService)
		if !ok || got != svc {
			c.Status(http.StatusInternalServerError)
			return
		}
		c.Status(http.StatusOK)
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/test", nil)
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", w.Code)
	}
}

// --- unmarshalOrderFromQueue ---

func TestUnmarshalOrderFromQueue(t *testing.T) {
	tests := []struct {
		name        string
		input       []byte
		expectError bool
		checkFields bool
	}{
		{
			name:        "valid order with items",
			input:       []byte(`{"customerId":"cust1","items":[{"productId":1,"quantity":2,"price":9.99}],"status":0}`),
			expectError: false,
			checkFields: true,
		},
		{
			name:        "valid order with empty items",
			input:       []byte(`{"customerId":"cust2","items":[],"status":0}`),
			expectError: false,
			checkFields: true,
		},
		{
			name:        "invalid JSON",
			input:       []byte(`not valid json`),
			expectError: true,
		},
		{
			name:        "empty input",
			input:       []byte(``),
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			order, err := unmarshalOrderFromQueue(tt.input)
			if tt.expectError {
				if err == nil {
					t.Error("expected error but got nil")
				}
				return
			}
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if tt.checkFields {
				if order.OrderID == "" {
					t.Error("expected non-empty OrderID after unmarshal")
				}
				if order.Status != Pending {
					t.Errorf("expected Status to be Pending (%d), got %d", Pending, order.Status)
				}
			}
		})
	}
}

// --- getOrder handler ---

func TestGetOrder(t *testing.T) {
	tests := []struct {
		name           string
		orderIDParam   string
		mockGetOrder   func(id string) (Order, error)
		expectedStatus int
		expectedID     string
	}{
		{
			name:         "returns order for valid numeric ID",
			orderIDParam: "42",
			mockGetOrder: func(id string) (Order, error) {
				return Order{OrderID: id, CustomerID: "cust1"}, nil
			},
			expectedStatus: http.StatusOK,
			expectedID:     "42",
		},
		{
			name:           "returns 400 for non-numeric ID",
			orderIDParam:   "abc",
			expectedStatus: http.StatusBadRequest,
		},
		{
			name:         "returns 500 when repo returns error",
			orderIDParam: "99",
			mockGetOrder: func(id string) (Order, error) {
				return Order{}, errors.New("db unavailable")
			},
			expectedStatus: http.StatusInternalServerError,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mock := &mockOrderRepo{getOrderFunc: tt.mockGetOrder}
			router := setupTestRouter(mock)

			w := httptest.NewRecorder()
			req, _ := http.NewRequest(http.MethodGet, "/order/"+tt.orderIDParam, nil)
			router.ServeHTTP(w, req)

			if w.Code != tt.expectedStatus {
				t.Errorf("expected status %d, got %d", tt.expectedStatus, w.Code)
			}

			if tt.expectedID != "" {
				var got Order
				if err := json.Unmarshal(w.Body.Bytes(), &got); err != nil {
					t.Fatalf("failed to decode response body: %v", err)
				}
				if got.OrderID != tt.expectedID {
					t.Errorf("expected OrderID %q, got %q", tt.expectedID, got.OrderID)
				}
			}
		})
	}
}

// --- updateOrder handler ---

func TestUpdateOrder(t *testing.T) {
	tests := []struct {
		name           string
		order          Order
		mockUpdate     func(order Order) error
		expectedStatus int
	}{
		{
			name:  "successfully updates a valid order",
			order: Order{OrderID: "7", CustomerID: "cust1", Status: Processing},
			mockUpdate: func(order Order) error {
				return nil
			},
			expectedStatus: http.StatusOK,
		},
		{
			name:           "returns 400 for non-numeric order ID",
			order:          Order{OrderID: "xyz", CustomerID: "cust1"},
			expectedStatus: http.StatusBadRequest,
		},
		{
			name:  "returns 500 when repo update fails",
			order: Order{OrderID: "5", CustomerID: "cust2"},
			mockUpdate: func(order Order) error {
				return errors.New("write failed")
			},
			expectedStatus: http.StatusInternalServerError,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mock := &mockOrderRepo{updateOrderFunc: tt.mockUpdate}
			router := setupTestRouter(mock)

			body, _ := json.Marshal(tt.order)
			w := httptest.NewRecorder()
			req, _ := http.NewRequest(http.MethodPut, "/order", bytes.NewBuffer(body))
			req.Header.Set("Content-Type", "application/json")
			router.ServeHTTP(w, req)

			if w.Code != tt.expectedStatus {
				t.Errorf("expected status %d, got %d", tt.expectedStatus, w.Code)
			}
		})
	}
}

// --- fetchOrders handler (error paths that don't require a running queue) ---

func TestFetchOrdersQueueNotConfigured(t *testing.T) {
	// When ORDER_QUEUE_NAME is not set, getOrdersFromQueue returns an error
	// immediately, causing fetchOrders to return 500.
	os.Unsetenv("ORDER_QUEUE_NAME")
	os.Unsetenv("ORDER_QUEUE_URI")

	mock := &mockOrderRepo{}
	router := setupTestRouter(mock)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/order/fetch", nil)
	router.ServeHTTP(w, req)

	if w.Code != http.StatusInternalServerError {
		t.Errorf("expected status 500, got %d", w.Code)
	}
}

// --- health endpoint ---

func TestHealthEndpoint(t *testing.T) {
	mock := &mockOrderRepo{}
	router := setupTestRouter(mock)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/health", nil)
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", w.Code)
	}

	var body map[string]interface{}
	if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
		t.Fatalf("failed to decode health response: %v", err)
	}
	if body["status"] != "ok" {
		t.Errorf("expected status 'ok', got %v", body["status"])
	}
}
