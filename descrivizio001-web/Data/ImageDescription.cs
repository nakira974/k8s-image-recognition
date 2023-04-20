using System.Text.Json.Serialization;

namespace ImageDescriptorV2.Data;

public class ImageDescription
{
    [JsonPropertyName("prediction")]
    public string? Prediction { get; set; }
}