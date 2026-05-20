package com.example.kabaaragent.data

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import retrofit2.http.Body
import retrofit2.http.POST

@Serializable
data class AppraisalRequest(
    val description: String,
    val image_base64: String? = null,
    val latitude: Double? = 33.60,
    val longitude: Double? = 73.06
)

@Serializable
data class ItemModel(
    val material_type: String,
    val estimated_weight_kg: Double,
    val purity_grade: String
)

@Serializable
data class PipelineResponse(
    val transaction_id: String,
    val items: List<ItemModel>,
    val valuation: Double,
    val optimal_yard: JsonObject? = null,
    val justification_log: String,
    val receipt: JsonObject? = null,
    val execution_trace: List<String>
)

interface KabaarApiService {
    @POST("api/pipeline")
    suspend fun runPipeline(@Body request: AppraisalRequest): PipelineResponse
}

object KabaarApiClient {
    private const val BASE_URL = "http://10.0.2.2:8000/"

    private val json = Json {
        ignoreUnknownKeys = true
        coerceInputValues = true
    }

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        })
        .build()

    val apiService: KabaarApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(KabaarApiService::class.java)
    }
}
