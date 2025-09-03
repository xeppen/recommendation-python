# 🚀 NestJS Implementation Guide - Rekryteringsrekommendationsmotor

## 📋 Migration Roadmap

### Phase 1: Core API Setup (Vecka 1-2)

#### Project Structure
```
apps/
├── recommendation-api/
│   ├── src/
│   │   ├── modules/
│   │   │   ├── recommendations/
│   │   │   ├── analytics/
│   │   │   ├── ml/
│   │   │   └── data/
│   │   ├── common/
│   │   ├── config/
│   │   └── main.ts
│   ├── test/
│   └── package.json
└── ml-service/  # Python microservice
    ├── src/
    │   ├── models/
    │   ├── services/
    │   └── api/
    └── requirements.txt
```

#### Core Dependencies
```bash
npm install @nestjs/core @nestjs/common @nestjs/config
npm install @google-cloud/bigquery redis ioredis
npm install @nestjs/bull bull
npm install class-validator class-transformer
npm install @nestjs/swagger
```

### Phase 2: Core Services Implementation

#### 1. Recommendations Module

```typescript
// recommendations.module.ts
@Module({
  imports: [
    ConfigModule,
    BullModule.registerQueue({
      name: 'ml-processing',
    }),
    CacheModule.register({
      ttl: 300, // 5 minutes
      max: 1000,
    }),
  ],
  controllers: [RecommendationsController],
  providers: [
    RecommendationsService,
    RoleSimilarityService,
    BudgetOptimizerService,
    PerformancePredictorService,
    BigQueryService,
  ],
  exports: [RecommendationsService],
})
export class RecommendationsModule {}

// recommendations.controller.ts
@Controller('api/v1/recommendations')
@ApiTags('recommendations')
export class RecommendationsController {
  constructor(
    private readonly recommendationsService: RecommendationsService
  ) {}

  @Post('generate')
  @ApiOperation({ summary: 'Generate channel and budget recommendations' })
  @ApiResponse({ type: RecommendationResponseDto })
  @UsePipes(new ValidationPipe({ transform: true }))
  @UseGuards(AuthGuard, RateLimitGuard)
  async generateRecommendation(
    @Body() request: RecommendationRequestDto,
    @Req() req: Request
  ): Promise<RecommendationResponseDto> {
    const startTime = Date.now();
    
    try {
      const result = await this.recommendationsService.generateRecommendation(request);
      
      // Log metrics
      this.metricsService.recordRecommendation(
        request.role,
        request.industry,
        Date.now() - startTime,
        'success'
      );
      
      return result;
    } catch (error) {
      this.metricsService.recordRecommendation(
        request.role,
        request.industry,
        Date.now() - startTime,
        'error'
      );
      throw error;
    }
  }

  @Get('similar-roles')
  @ApiOperation({ summary: 'Find similar roles for a given job title' })
  async findSimilarRoles(
    @Query('role') role: string,
    @Query('limit', new DefaultValuePipe(5), ParseIntPipe) limit: number
  ): Promise<SimilarRolesResponseDto> {
    return this.recommendationsService.findSimilarRoles(role, limit);
  }
}
```

#### 2. DTOs & Validation

```typescript
// dto/recommendation-request.dto.ts
export class RecommendationRequestDto {
  @IsString()
  @MinLength(2)
  @MaxLength(100)
  @ApiProperty({ example: 'Sjuksköterska', description: 'Job role to get recommendations for' })
  role: string;

  @IsOptional()
  @IsString()
  @ApiProperty({ example: 'Vård', description: 'Industry context', required: false })
  industry?: string;

  @IsOptional()
  @IsString()
  @ApiProperty({ example: 'Stockholm', description: 'Target location', required: false })
  location?: string;

  @IsEnum(BudgetTier)
  @ApiProperty({ enum: BudgetTier, example: BudgetTier.STANDARD })
  budgetTier: BudgetTier;

  @IsInt()
  @Min(1)
  @Max(365)
  @ApiProperty({ example: 30, description: 'Campaign duration in days' })
  campaignDays: number;
}

// dto/recommendation-response.dto.ts
export class RecommendationResponseDto {
  @ApiProperty()
  success: boolean;

  @ApiProperty({ type: RecommendationDataDto })
  data: RecommendationDataDto;

  @ApiProperty({ type: ResponseMetaDto })
  meta: ResponseMetaDto;
}

export class ChannelRecommendationDto {
  @ApiProperty({ enum: Platform })
  platform: Platform;

  @ApiProperty({ example: 3.11, description: 'Predicted CTR percentage' })
  predictedCtr: number;

  @ApiProperty({ example: 18.5, description: 'Predicted CPC in SEK' })
  predictedCpc: number;

  @ApiProperty({ example: 15000, description: 'Recommended budget in SEK' })
  recommendedBudget: number;

  @ApiProperty({ example: 811, description: 'Expected number of clicks' })
  expectedClicks: number;

  @ApiProperty({ enum: ConfidenceLevel })
  confidence: ConfidenceLevel;

  @ApiProperty({ example: 25, description: 'Number of historical campaigns' })
  historicalCampaigns: number;

  @ApiProperty({ type: [String], description: 'AI-generated insights' })
  insights: string[];

  @ApiProperty({ example: 85, description: 'Performance score 0-100' })
  performanceScore: number;
}
```

#### 3. BigQuery Service

```typescript
// bigquery.service.ts
@Injectable()
export class BigQueryService {
  private bigQuery: BigQuery;
  private readonly projectId: string;
  private readonly datasetId: string;

  constructor(private readonly configService: ConfigService) {
    this.projectId = this.configService.get<string>('GCP_PROJECT_ID');
    this.datasetId = this.configService.get<string>('GCP_DATASET_ID', 'recruitment_demo');
    
    this.bigQuery = new BigQuery({
      projectId: this.projectId,
      keyFilename: this.configService.get<string>('GCP_KEY_FILE'),
    });
  }

  @Cacheable('campaign-data', 3600) // Cache för 1 timme
  async getCampaignData(filters: CampaignFilters): Promise<Campaign[]> {
    const query = this.buildCampaignQuery(filters);
    
    try {
      const [rows] = await this.bigQuery.query(query);
      return rows.map(row => this.mapRowToCampaign(row));
    } catch (error) {
      this.logger.error('BigQuery query failed', error);
      throw new InternalServerErrorException('Failed to fetch campaign data');
    }
  }

  private buildCampaignQuery(filters: CampaignFilters): QueryOptions {
    let whereClause = "WHERE Campaign_Name NOT LIKE '%Employer Branding%'";
    const params: any = {};

    if (filters.role) {
      whereClause += " AND LOWER(Roll) = LOWER(@role)";
      params.role = filters.role;
    }

    if (filters.industry) {
      whereClause += " AND LOWER(Industry) = LOWER(@industry)";
      params.industry = filters.industry;
    }

    if (filters.platform) {
      whereClause += " AND Platform = @platform";
      params.platform = filters.platform;
    }

    const query = `
      SELECT 
        Roll,
        Storlek_pa_Stad,
        Location,
        Platform,
        Impressions,
        Clicks,
        Spend_SEK,
        CTR_Percent,
        CPC_SEK,
        Campaign_Days,
        Company,
        Campaign_Name
      FROM \`${this.projectId}.${this.datasetId}.campaigns\`
      ${whereClause}
      ORDER BY CTR_Percent DESC
      LIMIT 1000
    `;

    return { query, params };
  }
}
```

#### 4. ML Service Integration

```typescript
// ml.service.ts - Proxy till Python ML microservice
@Injectable()
export class MLService {
  private readonly mlServiceUrl: string;

  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService
  ) {
    this.mlServiceUrl = this.configService.get<string>('ML_SERVICE_URL', 'http://localhost:8000');
  }

  async generateEmbedding(text: string): Promise<number[]> {
    try {
      const response = await this.httpService.axiosRef.post(
        `${this.mlServiceUrl}/embeddings/generate`,
        { text },
        { timeout: 5000 }
      );
      
      return response.data.embedding;
    } catch (error) {
      this.logger.error('ML service call failed', error);
      throw new ServiceUnavailableException('ML service unavailable');
    }
  }

  @Cacheable('role-similarity', 1800) // Cache 30 min
  async findSimilarRoles(role: string, limit: number = 5): Promise<SimilarRole[]> {
    const response = await this.httpService.axiosRef.post(
      `${this.mlServiceUrl}/similarity/find-similar`,
      { role, limit }
    );
    
    return response.data.similar_roles;
  }

  async predictPerformance(
    role: string,
    platform: string,
    budget: number,
    historicalData: Campaign[]
  ): Promise<PerformancePrediction> {
    const response = await this.httpService.axiosRef.post(
      `${this.mlServiceUrl}/prediction/performance`,
      {
        role,
        platform,
        budget,
        historical_data: historicalData
      }
    );
    
    return response.data;
  }
}
```

### Python ML Microservice (FastAPI)

```python
# ml-service/main.py
from fastapi import FastAPI, HTTPException
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pandas as pd
from typing import List, Dict, Any
import uvicorn

app = FastAPI(title="ML Recommendation Service", version="1.0.0")

# Global models (ladda en gång vid startup)
sentence_model = None
faiss_index = None
role_mappings = None

@app.on_event("startup")
async def startup_event():
    global sentence_model, faiss_index, role_mappings
    
    # Ladda sentence transformer
    sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    # Ladda FAISS index
    faiss_index = faiss.read_index("models/role_index.faiss")
    
    # Ladda role mappings
    role_mappings = pd.read_csv("data/role_mappings.csv")
    
    print("✅ ML models loaded successfully")

@app.post("/embeddings/generate")
async def generate_embedding(request: dict):
    try:
        text = request.get("text", "")
        embedding = sentence_model.encode([text], normalize_embeddings=True)[0]
        return {"embedding": embedding.tolist()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/similarity/find-similar")
async def find_similar_roles(request: dict):
    try:
        role = request.get("role", "")
        limit = request.get("limit", 5)
        
        # Generate embedding
        query_embedding = sentence_model.encode([role], normalize_embeddings=True)
        
        # Search in FAISS
        scores, indices = faiss_index.search(query_embedding.astype('float32'), limit)
        
        # Map indices to roles
        similar_roles = []
        for idx, score in zip(indices[0], scores[0]):
            if score > 0.5:  # Threshold
                similar_roles.append({
                    "role": role_mappings.iloc[idx]['role'],
                    "similarity": float(score)
                })
        
        return {"similar_roles": similar_roles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/prediction/performance")
async def predict_performance(request: dict):
    try:
        role = request.get("role")
        platform = request.get("platform")
        budget = request.get("budget")
        historical_data = pd.DataFrame(request.get("historical_data", []))
        
        if historical_data.empty:
            raise HTTPException(status_code=400, detail="No historical data provided")
        
        # Filter for platform
        platform_data = historical_data[historical_data['Platform'] == platform]
        
        if platform_data.empty:
            # Fallback to similar platforms or general average
            platform_data = historical_data
        
        # Calculate weighted averages
        predicted_ctr = platform_data['CTR_Percent'].mean()
        predicted_cpc = platform_data['CPC_SEK'].mean()
        
        # Confidence based on sample size
        confidence = 'high' if len(platform_data) > 10 else 'medium' if len(platform_data) > 5 else 'low'
        
        return {
            "predicted_ctr": predicted_ctr,
            "predicted_cpc": predicted_cpc,
            "expected_clicks": int(budget / predicted_cpc) if predicted_cpc > 0 else 0,
            "confidence": confidence,
            "sample_size": len(platform_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 🔧 Configuration Management

### Environment Configuration

```typescript
// config/app.config.ts
export interface AppConfig {
  port: number;
  environment: string;
  apiPrefix: string;
  
  // Database
  bigquery: {
    projectId: string;
    datasetId: string;
    keyFile: string;
  };
  
  // Redis
  redis: {
    host: string;
    port: number;
    password?: string;
  };
  
  // ML Service
  mlService: {
    url: string;
    timeout: number;
    retries: number;
  };
  
  // OpenAI
  openai: {
    apiKey: string;
    model: string;
    maxTokens: number;
  };
  
  // Rate limiting
  rateLimit: {
    windowMs: number;
    max: number;
  };
}

export default (): AppConfig => ({
  port: parseInt(process.env.PORT, 10) || 3000,
  environment: process.env.NODE_ENV || 'development',
  apiPrefix: 'api/v1',
  
  bigquery: {
    projectId: process.env.GCP_PROJECT_ID,
    datasetId: process.env.GCP_DATASET_ID || 'recruitment_demo',
    keyFile: process.env.GCP_KEY_FILE,
  },
  
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT, 10) || 6379,
    password: process.env.REDIS_PASSWORD,
  },
  
  mlService: {
    url: process.env.ML_SERVICE_URL || 'http://localhost:8000',
    timeout: 10000,
    retries: 3,
  },
  
  openai: {
    apiKey: process.env.OPENAI_API_KEY,
    model: process.env.OPENAI_MODEL || 'gpt-3.5-turbo',
    maxTokens: 150,
  },
  
  rateLimit: {
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // Max 100 requests per window
  },
});
```

---

## 🧪 Testing Strategy

### Unit Tests

```typescript
// recommendations.service.spec.ts
describe('RecommendationsService', () => {
  let service: RecommendationsService;
  let bigQueryService: jest.Mocked<BigQueryService>;
  let mlService: jest.Mocked<MLService>;

  beforeEach(async () => {
    const module = await Test.createTestingModule({
      providers: [
        RecommendationsService,
        {
          provide: BigQueryService,
          useValue: {
            getCampaignData: jest.fn(),
          },
        },
        {
          provide: MLService,
          useValue: {
            findSimilarRoles: jest.fn(),
            predictPerformance: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get<RecommendationsService>(RecommendationsService);
    bigQueryService = module.get(BigQueryService);
    mlService = module.get(MLService);
  });

  describe('generateRecommendation', () => {
    it('should generate recommendations for known role', async () => {
      // Arrange
      const request = {
        role: 'Sjuksköterska',
        industry: 'Vård',
        budgetTier: BudgetTier.STANDARD,
        campaignDays: 30,
      };

      mlService.findSimilarRoles.mockResolvedValue([
        { role: 'Sjuksköterska', similarity: 0.95 },
      ]);

      bigQueryService.getCampaignData.mockResolvedValue([
        createMockCampaign({ role: 'Sjuksköterska', platform: 'Facebook' }),
      ]);

      // Act
      const result = await service.generateRecommendation(request);

      // Assert
      expect(result.success).toBe(true);
      expect(result.data.roleMatch.similarityScore).toBeGreaterThan(0.9);
      expect(result.data.channelRecommendations).toHaveLength(1);
      expect(result.data.channelRecommendations[0].platform).toBe('Facebook');
    });

    it('should handle unknown role gracefully', async () => {
      // Arrange
      const request = {
        role: 'Astronaut',
        budgetTier: BudgetTier.STANDARD,
        campaignDays: 30,
      };

      mlService.findSimilarRoles.mockResolvedValue([]);

      // Act & Assert
      await expect(service.generateRecommendation(request))
        .rejects.toThrow(InsufficientDataException);
    });
  });
});
```

### Integration Tests

```typescript
// test/recommendations.e2e-spec.ts
describe('RecommendationsController (e2e)', () => {
  let app: INestApplication;

  beforeEach(async () => {
    const moduleFixture = await Test.createTestingModule({
      imports: [AppModule],
    })
    .overrideProvider(BigQueryService)
    .useValue(createMockBigQueryService())
    .compile();

    app = moduleFixture.createNestApplication();
    await app.init();
  });

  it('/api/v1/recommendations/generate (POST)', () => {
    return request(app.getHttpServer())
      .post('/api/v1/recommendations/generate')
      .send({
        role: 'Sjuksköterska',
        industry: 'Vård',
        budgetTier: 'standard',
        campaignDays: 30,
      })
      .expect(201)
      .expect((res) => {
        expect(res.body.success).toBe(true);
        expect(res.body.data.channelRecommendations).toBeDefined();
      });
  });
});
```

---

## 📊 Monitoring & Observability

### Prometheus Metrics

```typescript
// metrics.service.ts
@Injectable()
export class MetricsService {
  private readonly recommendationCounter = new Counter({
    name: 'recommendations_total',
    help: 'Total recommendations generated',
    labelNames: ['role', 'industry', 'status', 'confidence'],
  });

  private readonly recommendationDuration = new Histogram({
    name: 'recommendation_duration_seconds',
    help: 'Recommendation generation time',
    labelNames: ['role', 'complexity'],
    buckets: [0.1, 0.5, 1, 2, 5, 10],
  });

  private readonly mlServiceCalls = new Counter({
    name: 'ml_service_calls_total',
    help: 'ML service API calls',
    labelNames: ['endpoint', 'status'],
  });

  private readonly cacheHitRate = new Counter({
    name: 'cache_hits_total',
    help: 'Cache hit/miss statistics',
    labelNames: ['type', 'result'],
  });

  recordRecommendation(
    role: string,
    industry: string,
    duration: number,
    status: string,
    confidence: string
  ) {
    this.recommendationCounter.inc({ role, industry, status, confidence });
    this.recommendationDuration.observe(
      { role, complexity: this.calculateComplexity(role) },
      duration / 1000
    );
  }

  recordMLServiceCall(endpoint: string, status: string) {
    this.mlServiceCalls.inc({ endpoint, status });
  }

  recordCacheAccess(type: string, hit: boolean) {
    this.cacheHitRate.inc({ type, result: hit ? 'hit' : 'miss' });
  }
}
```

### Logging Strategy

```typescript
// logger.service.ts
@Injectable()
export class CustomLogger extends Logger {
  log(message: string, context?: string) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      level: 'info',
      message,
      context,
      service: 'recommendation-api',
      environment: process.env.NODE_ENV,
    };
    
    console.log(JSON.stringify(logEntry));
  }

  error(message: string, trace?: string, context?: string) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      level: 'error',
      message,
      trace,
      context,
      service: 'recommendation-api',
      environment: process.env.NODE_ENV,
    };
    
    console.error(JSON.stringify(logEntry));
    
    // Send to error tracking service
    this.sendToSentry(logEntry);
  }
}
```

---

## 🚀 Deployment Strategy

### Docker Setup

```dockerfile
# Dockerfile för NestJS API
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

FROM node:18-alpine AS production

WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .

RUN npm run build

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

CMD ["node", "dist/main"]
```

```dockerfile
# Dockerfile för Python ML Service  
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Manifests

```yaml
# k8s/recommendation-api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recommendation-api
  labels:
    app: recommendation-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: recommendation-api
  template:
    metadata:
      labels:
        app: recommendation-api
    spec:
      containers:
      - name: api
        image: gcr.io/we-select-data-dev/recommendation-api:latest
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "production"
        - name: GCP_PROJECT_ID
          valueFrom:
            secretKeyRef:
              name: gcp-credentials
              key: project_id
        - name: REDIS_HOST
          value: "redis-service"
        - name: ML_SERVICE_URL
          value: "http://ml-service:8000"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: recommendation-api-service
spec:
  selector:
    app: recommendation-api
  ports:
  - port: 80
    targetPort: 3000
  type: LoadBalancer
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy Recommendation Service

on:
  push:
    branches: [main]
    paths: ['apps/recommendation-api/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: |
        cd apps/recommendation-api
        npm ci
    
    - name: Run tests
      run: |
        cd apps/recommendation-api
        npm run test
        npm run test:e2e
    
    - name: Run linting
      run: |
        cd apps/recommendation-api
        npm run lint

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Google Cloud CLI
      uses: google-github-actions/setup-gcloud@v1
      with:
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        project_id: ${{ secrets.GCP_PROJECT_ID }}
    
    - name: Build Docker image
      run: |
        cd apps/recommendation-api
        docker build -t gcr.io/${{ secrets.GCP_PROJECT_ID }}/recommendation-api:${{ github.sha }} .
    
    - name: Push to Container Registry
      run: |
        docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/recommendation-api:${{ github.sha }}
    
    - name: Deploy to GKE
      run: |
        gcloud container clusters get-credentials production-cluster --zone=europe-north1-a
        kubectl set image deployment/recommendation-api api=gcr.io/${{ secrets.GCP_PROJECT_ID }}/recommendation-api:${{ github.sha }}
        kubectl rollout status deployment/recommendation-api
```

---

## 📈 Performance Optimization

### Database Optimization

```sql
-- Optimized queries med proper indexing
CREATE INDEX CONCURRENTLY idx_campaigns_role_gin ON campaigns 
USING GIN(to_tsvector('swedish', Roll));

CREATE INDEX idx_campaigns_performance ON campaigns(CTR_Percent DESC, CPC_SEK ASC)
WHERE CTR_Percent > 0;

CREATE INDEX idx_campaigns_composite ON campaigns(Roll, Platform, Industry, CTR_Percent);

-- Partitioning för stora datasets
CREATE TABLE campaigns_partitioned (
  LIKE campaigns INCLUDING ALL
) PARTITION BY RANGE (created_at);

CREATE TABLE campaigns_2024 PARTITION OF campaigns_partitioned
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### Connection Pooling

```typescript
// database.config.ts
export const bigQueryConfig = {
  projectId: process.env.GCP_PROJECT_ID,
  maxRetries: 3,
  autoRetry: true,
  maxRetryDelay: 60000,
  
  // Connection pooling
  pool: {
    min: 2,
    max: 10,
    acquireTimeoutMillis: 30000,
    idleTimeoutMillis: 30000,
  },
  
  // Query optimization
  jobTimeoutMs: 300000, // 5 minutes
  maxResults: 10000,
  useLegacySql: false,
};
```

### Memory Management

```typescript
// memory-efficient data processing
@Injectable()
export class DataProcessingService {
  async processLargeDataset(campaigns: Campaign[]): Promise<ProcessedData> {
    // Stream processing för stora datasets
    const chunkSize = 1000;
    const results = [];
    
    for (let i = 0; i < campaigns.length; i += chunkSize) {
      const chunk = campaigns.slice(i, i + chunkSize);
      const processed = await this.processChunk(chunk);
      results.push(processed);
      
      // Yield control för att undvika blocking
      await new Promise(resolve => setImmediate(resolve));
    }
    
    return this.aggregateResults(results);
  }
  
  private async processChunk(chunk: Campaign[]): Promise<any> {
    return chunk.map(campaign => ({
      role: campaign.role,
      performance_score: this.calculatePerformanceScore(campaign),
      // Minimera minnesanvändning
    }));
  }
}
```

---

## 🔐 Security Best Practices

### Authentication & Authorization

```typescript
// auth.guard.ts
@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {
  canActivate(context: ExecutionContext): boolean | Promise<boolean> {
    const request = context.switchToHttp().getRequest();
    
    // Skip auth för health checks
    if (request.url.includes('/health')) {
      return true;
    }
    
    return super.canActivate(context);
  }
}

// roles.guard.ts  
@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredRoles = this.reflector.getAllAndOverride<Role[]>('roles', [
      context.getHandler(),
      context.getClass(),
    ]);
    
    if (!requiredRoles) {
      return true;
    }
    
    const { user } = context.switchToHttp().getRequest();
    return requiredRoles.some((role) => user.roles?.includes(role));
  }
}
```

### Input Sanitization

```typescript
// sanitization.pipe.ts
@Injectable()
export class SanitizationPipe implements PipeTransform {
  transform(value: any): any {
    if (typeof value === 'string') {
      // Ta bort potentiellt farliga tecken
      return value
        .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
        .replace(/javascript:/gi, '')
        .trim();
    }
    
    if (typeof value === 'object' && value !== null) {
      const sanitized = {};
      for (const [key, val] of Object.entries(value)) {
        sanitized[key] = this.transform(val);
      }
      return sanitized;
    }
    
    return value;
  }
}
```

---

## 🎯 Business Logic Implementation

### Recommendation Algorithm

```typescript
@Injectable()
export class RecommendationEngine {
  async generateChannelMix(
    role: string,
    industry: string,
    budget: number,
    historicalData: Campaign[]
  ): Promise<ChannelRecommendation[]> {
    
    // 1. Analysera platform performance
    const platformPerformance = this.analyzePlatformPerformance(historicalData);
    
    // 2. Beräkna optimal budget allocation
    const budgetAllocation = this.optimizeBudgetAllocation(platformPerformance, budget);
    
    // 3. Generera rekommendationer
    const recommendations = await Promise.all(
      Object.entries(budgetAllocation).map(async ([platform, allocatedBudget]) => {
        const prediction = await this.mlService.predictPerformance(
          role,
          platform,
          allocatedBudget,
          historicalData.filter(c => c.platform === platform)
        );
        
        return {
          platform: platform as Platform,
          predictedCtr: prediction.predicted_ctr,
          predictedCpc: prediction.predicted_cpc,
          recommendedBudget: allocatedBudget,
          expectedClicks: prediction.expected_clicks,
          confidence: prediction.confidence,
          historicalCampaigns: historicalData.filter(c => c.platform === platform).length,
          insights: await this.generatePlatformInsights(platform, prediction),
          performanceScore: this.calculatePerformanceScore(prediction)
        };
      })
    );
    
    return recommendations.sort((a, b) => b.performanceScore - a.performanceScore);
  }

  private analyzePlatformPerformance(campaigns: Campaign[]): Map<string, PlatformMetrics> {
    const platformStats = new Map();
    
    for (const campaign of campaigns) {
      if (!platformStats.has(campaign.platform)) {
        platformStats.set(campaign.platform, {
          campaigns: [],
          totalSpend: 0,
          totalClicks: 0,
          totalImpressions: 0
        });
      }
      
      const stats = platformStats.get(campaign.platform);
      stats.campaigns.push(campaign);
      stats.totalSpend += campaign.spendSEK;
      stats.totalClicks += campaign.clicks;
      stats.totalImpressions += campaign.impressions;
    }
    
    // Beräkna aggregerad statistik
    for (const [platform, stats] of platformStats.entries()) {
      stats.avgCtr = (stats.totalClicks / stats.totalImpressions) * 100;
      stats.avgCpc = stats.totalSpend / stats.totalClicks;
      stats.campaignCount = stats.campaigns.length;
      stats.consistency = this.calculateConsistency(stats.campaigns);
    }
    
    return platformStats;
  }

  private optimizeBudgetAllocation(
    platformPerformance: Map<string, PlatformMetrics>,
    totalBudget: number
  ): Record<string, number> {
    // Portfolio optimization approach
    const platforms = Array.from(platformPerformance.keys());
    const scores = platforms.map(p => this.calculatePlatformScore(platformPerformance.get(p)));
    
    // Normalisera scores till weights
    const totalScore = scores.reduce((sum, score) => sum + score, 0);
    const weights = scores.map(score => score / totalScore);
    
    // Allokera budget baserat på weights
    const allocation = {};
    for (let i = 0; i < platforms.length; i++) {
      allocation[platforms[i]] = Math.round(totalBudget * weights[i]);
    }
    
    return allocation;
  }
}
```

Detta är en komplett teknisk dokumentation som ger dig allt du behöver för att implementera systemet i NestJS! 🚀
