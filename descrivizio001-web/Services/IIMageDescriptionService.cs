using ImageDescriptorV2.Data;

namespace ImageAnalyzerV1.Services;

public interface IIMageDescriptionService
{
    public Task<ImageDescription?> GetImageDescription(String imageUrl);
}