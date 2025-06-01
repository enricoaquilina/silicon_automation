# SiliconSentiments MongoDB MCP Server

A Model Context Protocol (MCP) server for analyzing and managing SiliconSentiments Art data stored in MongoDB. This server provides powerful tools for content analysis, automated image generation, and brand development.

## 🎯 Features

### **Data Analysis**
- Database statistics and collection analysis
- Post analysis (published, unpublished, missing images)
- Content theme analysis from prompts and descriptions
- Posting pattern analysis for optimization

### **Automated Image Generation**
- Integration with multi-provider image generation system
- Automatic detection of posts needing images
- Brand-consistent prompt generation
- Cost tracking and performance analysis

### **Instagram Analysis**
- Historical posting pattern analysis
- Success pattern identification
- Content theme extraction
- Brand development suggestions

### **Brand Intelligence**
- Style pattern analysis from successful posts
- Prompt optimization recommendations
- Engagement trend analysis
- Content improvement suggestions

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy configuration
cp config.example.json config.json
```

### 2. Configuration

Edit `config.json` with your settings:

```json
{
  "mongodb": {
    "uri": "mongodb://your_pi_ip:27017/",
    "database": "silicon_sentiments"
  },
  "image_generation": {
    "providers": {
      "replicate": {
        "api_token": "your_replicate_token"
      }
    }
  }
}
```

### 3. Running the Server

```bash
python server.py
```

The server will start and listen for MCP protocol connections.

## 🛠️ Available Tools

### **Connection Management**
- `connect_mongodb` - Connect to MongoDB on your Raspberry Pi
- `close_connection` - Close MongoDB connection

### **Data Analysis**
- `get_database_stats` - Get database statistics and collection info
- `analyze_posts` - Analyze posts for missing images and patterns
- `get_posts_needing_images` - Find posts that need images generated
- `get_successful_posts` - Get successfully published posts for analysis

### **Content Analysis** 
- `analyze_style_patterns` - Analyze prompts and styles from successful posts
- `analyze_posting_patterns` - Analyze historical posting patterns
- `analyze_content_themes` - Analyze content themes from prompts
- `identify_success_patterns` - Identify patterns in successful content

### **Image Generation**
- `generate_missing_images` - Generate images for posts missing them
- `analyze_generation_performance` - Analyze automated generation performance

### **Brand Development**
- `suggest_improvements` - Get content and posting suggestions

## 📊 Usage Examples

### Connect to Your MongoDB

```json
{
  "tool": "connect_mongodb",
  "arguments": {
    "mongodb_uri": "mongodb://192.168.1.100:27017/",
    "db_name": "silicon_sentiments"
  }
}
```

### Analyze Your Data

```json
{
  "tool": "analyze_posts"
}
```

### Get Posts Needing Images

```json
{
  "tool": "get_posts_needing_images",
  "arguments": {
    "limit": 10
  }
}
```

### Generate Missing Images

```json
{
  "tool": "generate_missing_images",
  "arguments": {
    "max_generations": 5,
    "config": {
      "providers": {
        "replicate": {
          "api_token": "your_token",
          "default_model": "flux_dev"
        }
      }
    }
  }
}
```

### Analyze Content Themes

```json
{
  "tool": "analyze_content_themes"
}
```

### Get Improvement Suggestions

```json
{
  "tool": "suggest_improvements"
}
```

## 🎨 Integration with Image Generation

The MCP server integrates with your multi-provider image generation system:

1. **Identifies missing images** from your MongoDB data
2. **Generates brand-consistent prompts** based on SiliconSentiments aesthetic
3. **Uses cost-optimized providers** (Replicate as backup to Midjourney)
4. **Saves results to MongoDB/GridFS** for Instagram publisher integration
5. **Tracks performance** and costs for optimization

### Brand-Consistent Generation

The server automatically enhances prompts with SiliconSentiments branding:

```
Original: "abstract digital landscape"
Enhanced: "abstract digital landscape, digital art, modern, clean aesthetic, 
          tech-inspired, vibrant colors, high contrast, instagram ready"
```

## 📈 Analytics & Insights

### Posting Pattern Analysis
- Best posting times and frequencies
- Day-of-week performance patterns
- Seasonal content trends
- Engagement optimization suggestions

### Content Theme Analysis
- Most successful art themes
- Prompt keyword frequency
- Style preferences (realistic vs abstract)
- Midjourney parameter optimization

### Success Pattern Identification
- Characteristics of published vs unpublished content
- Provider performance comparison
- Cost vs quality analysis
- Brand consistency metrics

## 🔮 Future Instagram Integration

The MCP server is designed to integrate with Instagram's API for:

### **Feed Analysis**
- Analyze competitor content for inspiration
- Track trending hashtags and styles
- Identify engagement patterns
- Content gap analysis

### **Automated Posting**
- Schedule posts based on optimal timing
- Queue content for consistent posting
- A/B test different content types
- Performance tracking and optimization

### **Brand Development**
- Track brand mention sentiment
- Analyze audience engagement preferences
- Identify successful content formats
- Optimize posting strategy

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server                               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   MongoDB   │  │   Image     │  │ Instagram   │         │
│  │  Analysis   │  │ Generation  │  │  Analysis   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────────────┐
                    │ MongoDB/GridFS  │
                    │ (Raspberry Pi)  │
                    └─────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
    ┌───────────────┐ ┌──────────────┐ ┌──────────────┐
    │ Multi-Provider│ │   Instagram  │ │   Future     │
    │ Image Gen     │ │   Publisher  │ │   Integrations│
    └───────────────┘ └──────────────┘ └──────────────┘
```

## 🔧 Configuration Options

### MongoDB Settings
- **uri**: Connection string to your Raspberry Pi MongoDB
- **database**: Database name (default: silicon_sentiments)

### Image Generation Settings
- **providers**: Configuration for Replicate, Midjourney, etc.
- **default_strategy**: brand_optimized, cost_optimized, speed_optimized
- **max_concurrent_generations**: Parallel generation limit
- **max_cost_per_generation**: Cost control

### Brand Settings
- **style_prompts**: Base prompts for brand consistency
- **negative_prompts**: Terms to avoid in generation
- **preferred_dimensions**: Default image dimensions

### Automation Settings
- **auto_generate_missing**: Automatically generate missing images
- **max_daily_generations**: Limit on daily automated generations
- **analysis_frequency**: How often to run analysis

## 📚 Data Schema

The server works with your existing MongoDB schema:

### Posts Collection
```json
{
  "_id": "ObjectId",
  "shortcode": "unique_identifier",
  "image_ref": "ObjectId_reference_to_post_images",
  "instagram_status": "published|pending|failed",
  "instagram_post_id": "published_post_id",
  "instagram_publish_date": "datetime",
  "automated_generation": {
    "generated_at": "datetime",
    "provider": "replicate|midjourney",
    "cost": 0.05,
    "status": "completed"
  }
}
```

### Post Images Collection
```json
{
  "_id": "ObjectId",
  "images": [{
    "midjourney_generations": [{
      "variation": "v6.0|v6.1|niji",
      "midjourney_image_id": "GridFS_file_id",
      "prompt": "original_prompt",
      "post_id": "correlation_id"
    }]
  }]
}
```

## 🎯 Benefits for SiliconSentiments Art

1. **Resume Daily Posting**: Identify and generate missing images automatically
2. **Data-Driven Decisions**: Analyze what content performs best
3. **Cost Optimization**: Use cheaper providers for iterations, premium for finals
4. **Brand Consistency**: Maintain SiliconSentiments aesthetic across all content
5. **Scalable Growth**: Automated analysis and generation as you scale
6. **Performance Tracking**: Monitor costs, success rates, and engagement

## 🚨 Error Handling

The server includes comprehensive error handling:
- MongoDB connection failures
- Image generation provider errors
- Rate limiting and quota management
- Data validation and sanitization
- Graceful degradation when services are unavailable

## 📞 Support & Troubleshooting

### Common Issues
1. **MongoDB connection fails**: Check Raspberry Pi IP and MongoDB service
2. **Image generation fails**: Verify API tokens and provider status
3. **No posts found**: Confirm database name and collection structure
4. **High costs**: Review generation limits and provider selection

### Debugging
- Check server logs for detailed error messages
- Verify configuration file format
- Test MongoDB connectivity separately
- Validate API tokens with provider

---

*This MCP server provides the foundation for analyzing your SiliconSentiments Art data and automating content creation. It integrates seamlessly with your existing MongoDB setup and image generation system.*